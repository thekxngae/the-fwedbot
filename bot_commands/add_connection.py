from telegram import CallbackQuery
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from GLOSSARY import logger, SK_ADD1, SK_ADD2, Correct_Input_Format, SK_ADD3, SK_ADD4, SK_ADD5, SK_ADD6, SK_START
from bot_functions.main.forwarding import handle_message
from database.db_manager import execute_non_query, execute_query
from database.db_setup import SQL_NEXT_STEP
from database.db_user_queries import get_user_groups

input_format = Correct_Input_Format

async def step_checker(user_id: int, expected_step: str) -> bool:
    query_current_step = "SELECT current_step FROM user_states WHERE user_id = ?;"
    result = execute_query(query_current_step, params=(user_id,))

    # Extract current step (log value for debugging)
    current_step = result[0][0] if result else None
    logger.info(f"[STEP CHECK] User {user_id} current step in DB: '{current_step}', Expected: '{expected_step}'")

    # Compare actual result with the expected step
    return current_step == expected_step

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_step = SK_ADD1
    next_step = SQL_NEXT_STEP

    # Update user's "Current Step" in user_states
    try:
        try:
            logger.info(f"Executing query: {next_step}, with params: {(current_step, user_id)}")
            execute_non_query(query=next_step, params=(current_step, user_id))
        except Exception as e:
            logger.error(
                f"[SQL ERROR] Query failed: {next_step} - Params: {(current_step, user_id)} - Error: {e}")

        logger.info(f"[CONNECTION] Updated user {user_id} current step to {current_step}.")

        # Verify update
        fetch_query = "SELECT current_step FROM user_states WHERE user_id = ?;"
        updated_result = execute_query(fetch_query, params=(user_id,))

        if not updated_result or updated_result[0][0] != current_step:
            logger.error(
                f"[VERIFICATION FAILED] User {user_id} current_step verification failed. Expected: {current_step}, Found: {updated_result}")
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Failed to update your progress. Please try again.")
            return
    except Exception as e:
        logger.error(f"[DATABASE ERROR] Failed to update/verify current_step for user {user_id}: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An error occurred. Please try again later."
        )
        return

    logger.info(f"[CONNECTION] User {user_id} requested to add a new connection.")
    await context.bot.send_message(
        chat_id=chat_id,
        text="📝 You’ve started creating a new connection. Let’s start by naming this connection."
    )

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # ID of the user sending the message
    chat_id = update.effective_chat.id  # ID of the chat where the message is sent
    expected_step = SK_ADD1  # Workflow step where the user is expected to add a title
    current_step = SK_ADD2  # Workflow step to update after this one
    next_step = SQL_NEXT_STEP  # SQL query to update the next step
    chat_type = update.message.chat.type

    try:
        # Ignore messages from groups and supergroups for this step
        if chat_type in ["group", "supergroup"]:
            logger.info(f"[WARNING] Ignored message from user {user_id} in chat type '{chat_type}'.")
            await handle_message(update, context)
            return

        # Perform step check for private chats
        if not await step_checker(user_id, expected_step):
            logger.info(f"[STEP CHECK] Ignored message from user {user_id} not in step '{expected_step}'.")
            return

        # Get user message as connection title
        connection_title = update.message.text.strip()  # Get text input from user

        if not connection_title:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ No Input Detected. Please add a title for your new connection."
            )
            return

        # Insert placeholder connection into user_connections if it does not exist
        insert_query = """
            INSERT INTO user_connections (user_id, source_group_id, source_topic_id, target_group_id, target_topic_id, connection_title)
            VALUES (?, NULL, NULL, NULL, NULL, ?)
        """
        execute_non_query(insert_query, (user_id, connection_title))
        logger.info(f"[CONNECTION] Inserted new connection for user {user_id} with title '{connection_title}'.")

        # Fetch the newly inserted connection_id
        fetch_id_query = """
            SELECT connection_id FROM user_connections
            WHERE user_id = ? AND connection_title = ?
            ORDER BY connection_id DESC LIMIT 1
        """
        result = execute_query(fetch_id_query, (user_id, connection_title))
        if result and result[0]:
            connection_id = result[0][0]
            context.user_data['connection_id'] = connection_id  # Save for later stages
            logger.info(f"[CONNECTION ID] Retrieved connection_id {connection_id} for user {user_id}.")
        else:
            logger.error("[CONNECTION ID] Failed to fetch connection_id after insert.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Failed to create a new connection. Please try again."
            )
            return

        # Update the user's "Current Step" in user_states
        try:
            logger.info(f"Executing query: {next_step}, with params: {(current_step, user_id)}")
            execute_non_query(query=next_step, params=(current_step, user_id))

            logger.info(f"[CONNECTION] Updated user {user_id}'s current step to {current_step}.")

            # Verify update
            fetch_query = "SELECT current_step FROM user_states WHERE user_id = ?;"
            updated_result = execute_query(fetch_query, params=(user_id,))

            if not updated_result or updated_result[0][0] != current_step:
                logger.error(
                    f"[VERIFICATION FAILED] User {user_id} current_step verification failed. Expected: {current_step}, Found: {updated_result}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Failed to update your progress. Please try again."
                )
                return
        except Exception as e:
            logger.error(f"[DATABASE ERROR] Failed to update/verify current_step for user {user_id}: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ An error occurred. Please try again later."
            )
            return

        # Confirm success and print connection_id
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Connection `{connection_title}` has been named successfully! Your connection ID is `{connection_id}`."
        )

        # Trigger the next phase of the workflow
        await handle_ids(update, context)

    except Exception as error:
        logger.error(f"[CONNECTION] Failed to add connection title for user {user_id}: {error}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ An error occurred while adding your connection. Please try again later."
        )

async def handle_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    expected_step = SK_ADD2
    current_step = SK_ADD3
    next_step = SQL_NEXT_STEP

    try:
        # Step-checker to ensure the user is in the correct stage
        if not await step_checker(user_id, expected_step):
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the phase to add connection IDs. Restarting workflow...",
            )
            logger.warning(f"[STEP CHECK] User {user_id} is not in step '{SK_ADD2}' while trying to add IDs.")
            return  # Exit early

        # Fetch the list of groups the user has added to the bot
        user_groups = get_user_groups(user_id)
        if not user_groups:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ You have not added any groups to the bot yet. Please add fwedbot to the groups you want to configure.",
            )
            return

        # Display the groups as selectable buttons
        keyboard = [
            [InlineKeyboardButton(group_name, callback_data=f"source_group_{group_id}")]
            for group_id, group_name in user_groups
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text="Please select the source group for your connection:",
            reply_markup=reply_markup,
        )

        # Update user's "Current Step" in user_states
        try:
            try:
                logger.info(f"Executing query: {next_step}, with params: {(current_step, user_id)}")
                execute_non_query(query=next_step, params=(current_step, user_id))
            except Exception as e:
                logger.error(
                    f"[SQL ERROR] Query failed: {next_step} - Params: {(current_step, user_id)} - Error: {e}")

            logger.info(f"[CONNECTION] Updated user {user_id} current step to {current_step}.")

            # Verify update
            fetch_query = "SELECT current_step FROM user_states WHERE user_id = ?;"
            updated_result = execute_query(fetch_query, params=(user_id,))

            if not updated_result or updated_result[0][0] != current_step:
                logger.error(
                    f"[VERIFICATION FAILED] User {user_id} current_step verification failed. Expected: {current_step}, Found: {updated_result}")
                await context.bot.send_message(chat_id=chat_id,
                                               text="⚠️ Failed to update your progress. Please try again.")
                return
        except Exception as e:
            logger.error(f"[DATABASE ERROR] Failed to update/verify current_step for user {user_id}: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ An error occurred. Please try again later."
            )
            return

    except Exception as e:
        logger.error(f"[IDS Input Error] Unexpected error (user_id={user_id}): {str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An unexpected error occurred. Please try again or contact support.",
        )

async def handle_source_group_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    expected_step = SK_ADD3
    current_step = SK_ADD4
    connection_id = context.user_data.get("connection_id")
    next_step = SQL_NEXT_STEP

    query: CallbackQuery = update.callback_query
    await query.answer()  # Acknowledge callback query

    chat_id = update.effective_chat.id
    user_id = query.from_user.id

    try:
        # Step-checker to ensure the user is in the correct stage
        if not await step_checker(user_id, expected_step):
            logger.warning(f"[STEP CHECK] User {user_id} is not in step '{expected_step}' while trying to add IDs.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the correct stage. Restarting the workflow."
            )
            return

        # Handle callback data
        if query.data == "source_group_none":
            # Allow skipping if no source group is selected
            logger.info(f"[Group Selection] User {user_id} chose 'No specific group'.")
            context.user_data["source_group_id"] = None
            await context.bot.send_message(chat_id=chat_id, text="✅ No source group has been selected.")
        elif query.data.startswith("source_group_"):
            # Extract group_id from callback data
            callback_group_id = query.data.replace("source_group_", "").strip()

            # Fetch and validate the group from the database
            fetch_groups_query = "SELECT group_id, group_name FROM user_groups WHERE user_id = ?;"
            user_groups = execute_query(fetch_groups_query, (user_id,))
            if not user_groups:
                logger.warning(f"[Group Selection] No groups found for user_id {user_id}.")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ No groups are configured. Please add groups and try again."
                )
                return

            # Match the callback group_id to one in the user's groups
            matching_group = next((group for group in user_groups if str(group[0]) == callback_group_id), None)
            if not matching_group:
                logger.error(f"[Group Selection] Invalid group_id {callback_group_id} for user_id {user_id}.")
                await context.bot.send_message(chat_id=chat_id, text="❌ Selected group is invalid. Please try again.")
                return

            source_group_id, source_group_name = matching_group
            context.user_data["source_group_id"] = source_group_id

            # Update user connection with selected source group
            update_query = "UPDATE user_connections SET source_group_id = ? WHERE connection_id = ?;"
            execute_non_query(update_query, (source_group_id, connection_id))

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Group '{source_group_name}' has been selected as the source group."
            )
        else:
            raise ValueError(f"Unexpected callback data format: {query.data}")

        # Fetch topics for the selected source group
        source_group_id = context.user_data.get("source_group_id")
        group_topics = get_group_topics(source_group_id) if source_group_id else []
        if not group_topics:
            logger.warning(f"[Group Topics] No topics found for group_id {source_group_id}.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ No topics configured for this group. You can proceed by selecting 'No specific topic'."
            )

        # Display topics as selectable buttons
        keyboard = [
            [InlineKeyboardButton(topic_name, callback_data=f"source_topic_{topic_id}")]
            for topic_id, topic_name in group_topics
        ]
        keyboard.append([InlineKeyboardButton("No specific topic", callback_data="source_topic_none")])
        await context.bot.send_message(
            chat_id=chat_id,
            text="Please select the source topic for your connection:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Update user step state
        execute_non_query(next_step, (current_step, user_id))

    except Exception as e:
        logger.error(f"[Group Selection Error] User {user_id} encountered an error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An unexpected error occurred. Please restart the workflow and try again."
        )

def get_group_topics(group_id: int) -> list:
    try:
        # Log the group_id received
        logger.info(f"Received group_id: {group_id} Fetching topics for group_id: {group_id} (type: {type(group_id)})")

        # Query to fetch topics linked to the group_id
        query = """
            SELECT topic_id, topic_name FROM group_topics
            WHERE group_id = ?;
        """
        # Ensure group_id is passed as a tuple
        return execute_query(query=query, params=(group_id,))  # Params must be a tuple, e.g., (group_id,)
    except Exception as e:
        # Log any errors during query execution
        logger.error(f"[Fetching Topics Error] Could not fetch topics for group_id {group_id}: {e}")
        return []

async def handle_source_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()

    expected_step = SK_ADD4
    current_step = SK_ADD5
    next_step = SQL_NEXT_STEP

    user_id = query.from_user.id
    chat_id = update.effective_chat.id
    connection_id = context.user_data.get("connection_id")

    try:
        if not await step_checker(user_id, expected_step):
            logger.warning(f"[STEP CHECK] User {user_id} is not in step '{expected_step}' for source topic selection.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the correct stage. Restarting the workflow."
            )
            return

        # Handle callback data
        if query.data == "source_topic_none":
            context.user_data["source_topic_id"] = None
            await context.bot.send_message(
                chat_id=chat_id, text="✅ No source topic has been selected."
            )
        elif query.data.startswith("source_topic_"):
            callback_topic_id = query.data.replace("source_topic_", "").strip()
            context.user_data["source_topic_id"] = int(callback_topic_id)
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ Source topic has been successfully selected."
            )
        else:
            raise ValueError(f"Unexpected callback data format: {query.data}")

        # Fetch user groups to assign target group
        user_groups = get_user_groups(user_id)
        if not user_groups:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ You currently have no groups configured. Please add a group."
            )
            return

        # Create group selection buttons
        keyboard = [
            [InlineKeyboardButton(group_name, callback_data=f"target_group_{group_id}")]
            for group_id, group_name in user_groups
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="Please select the target group for your connection:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Update source_topic_id in the database
        source_topic_id = context.user_data.get("source_topic_id")
        update_query = """
            UPDATE user_connections
            SET source_topic_id = ?
            WHERE connection_id = ?;
        """
        execute_non_query(update_query, (source_topic_id, connection_id))
        logger.info(f"Updated source_topic_id {source_topic_id} for connection_id {connection_id}.")

        # Update user step state
        execute_non_query(next_step, (current_step, user_id))

    except Exception as e:
        logger.error(f"[Source Topic Selection Error] User {user_id} encountered an error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An error occurred. Please restart the workflow and try again."
        )

async def handle_target_group_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()

    expected_step = SK_ADD5
    current_step = SK_ADD6
    next_step = SQL_NEXT_STEP

    user_id = query.from_user.id
    chat_id = query.message.chat.id
    connection_id = context.user_data.get("connection_id")

    try:
        if not await step_checker(user_id, expected_step):
            logger.warning(f"[STEP CHECK] User {user_id} is not in step '{expected_step}' for target group selection.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the correct stage. Restarting the workflow."
            )
            return

        if query.data.startswith("target_group_"):
            callback_group_id = query.data.replace("target_group_", "").strip()
            context.user_data["target_group_id"] = int(callback_group_id)
            await context.bot.send_message(chat_id=chat_id, text="✅ Target group successfully selected.")
        else:
            raise ValueError(f"Unexpected callback data format: {query.data}")

        # Fetch target topics
        target_group_id = context.user_data.get("target_group_id")
        target_topics = get_group_topics(target_group_id) if target_group_id else []
        keyboard = [
            [InlineKeyboardButton(topic_name, callback_data=f"target_topic_{topic_id}")]
            for topic_id, topic_name in target_topics
        ]
        keyboard.append([InlineKeyboardButton("No specific topic", callback_data="target_topic_none")])
        await context.bot.send_message(
            chat_id=chat_id,
            text="Please select the target topic for your connection:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Update target_group_id in the database
        target_group_id = context.user_data.get("target_group_id")
        update_query = """
            UPDATE user_connections
            SET target_group_id = ?
            WHERE connection_id = ?;
        """
        execute_non_query(update_query, (target_group_id, connection_id))
        logger.info(f"Updated target_group_id {target_group_id} for connection_id {connection_id}.")

        # Update user step state
        execute_non_query(next_step, (current_step, user_id))

    except Exception as e:
        logger.error(f"[Target Group Selection Error] User {user_id} encountered an error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An error occurred. Please restart the workflow and try again."
        )

async def handle_target_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()

    expected_step = SK_ADD6
    current_step = SK_START
    next_step = SQL_NEXT_STEP

    user_id = query.from_user.id
    chat_id = query.message.chat.id
    connection_id = context.user_data.get("connection_id")

    try:
        if not await step_checker(user_id, expected_step):
            logger.warning(f"[STEP CHECK] User {user_id} is not in step '{expected_step}' for target topic selection.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the correct stage. Restarting the workflow."
            )
            return

        if query.data == "target_topic_none":
            context.user_data["target_topic_id"] = None
            await context.bot.send_message(
                chat_id=chat_id, text="✅ No target topic has been selected."
            )
        elif query.data.startswith("target_topic_"):
            callback_topic_id = query.data.replace("target_topic_", "").strip()
            context.user_data["target_topic_id"] = int(callback_topic_id)
            await context.bot.send_message(chat_id=chat_id, text="✅ Target topic successfully selected.")
        else:
            raise ValueError(f"Unexpected callback data format: {query.data}")

        # Complete the workflow
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 Connection Configuartion Complete! You can now create another connection or return to the main menu.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Return to Main Menu", callback_data="main_menu")]
            ])
        )

        # Update target_topic_id in the database
        target_topic_id = context.user_data.get("target_topic_id")
        update_query = """
            UPDATE user_connections
            SET target_topic_id = ?
            WHERE connection_id = ?;
        """
        execute_non_query(update_query, (target_topic_id, connection_id))
        logger.info(f"Updated target_topic_id {target_topic_id} for connection_id {connection_id}.")

        # Update user step state to reset
        execute_non_query(next_step, (current_step, user_id))

    except Exception as e:
        logger.error(f"[Target Topic Selection Error] User {user_id} encountered an error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An unexpected error occurred. Please restart the workflow and try again."
        )
