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

    if not query.data.startswith("source_group_"):
        raise ValueError(f"Unexpected callback data format: {query.data}")

    chat_id = update.effective_chat.id
    user_id = query.from_user.id

    logger.info(f"[Group Selection] Received callback data: {query.data}")

    try:
        # Step-checker to ensure the user is in the correct stage
        if not await step_checker(user_id, expected_step):
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the phase to add connection IDs. Restarting workflow...",
            )
            logger.warning(f"[STEP CHECK] User {user_id} is not in step '{SK_ADD3}' while trying to add IDs.")
            return  # Exit early

        # Extract group_id from callback data
        if query.data.startswith("source_group_"):
            callback_group_id = query.data.replace("source_group_", "").strip()
        else:
            raise ValueError(f"Unexpected callback data format: {query.data}")

        # Ensure callback_group_id is valid and exists in user_groups
        fetch_groups_query = """
            SELECT group_id, group_name FROM user_groups
            WHERE user_id = ?;
        """
        user_groups = execute_query(fetch_groups_query, (user_id,))

        if not user_groups:
            logger.warning(f"[Group Selection] No groups found for user_id: {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ No groups are configured for this user. Please add groups and try again. Use /help to learn how."
            )
            return

        # Match the callback group_id to one in the user's groups
        matching_group = next((group for group in user_groups if str(group[0]) == callback_group_id), None)

        if matching_group is None:
            logger.error(
                f"[Group Selection] Invalid group_id: {callback_group_id}, not found in user_groups for user_id: {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Selected group is invalid. Please try again."
            )
            return

        source_group_id, source_group_name = matching_group
        logger.info(f"[Group Selection] Matched group_id: {source_group_id}, group_name: {source_group_name}")

        # Save group_id in context.user_data
        context.user_data["source_group_id"] = source_group_id
        logger.info(f"`source_group_id` stored in user_data: {context.user_data.get('source_group_id')}")

        # Proceed with updating the database with the selected group
        update_query = """
            UPDATE user_connections
            SET source_group_id = ?
            WHERE connection_id = ?;
        """
        execute_non_query(update_query, (source_group_id, connection_id))
        logger.info(
            f"[CONNECTION] Updated connection_id {context.user_data.get('connection_id')} with source_group_id {source_group_id}")

        # Notify user of success
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Group '{source_group_name}' has been successfully selected as the source group."
        )

        group_topics = get_group_topics(source_group_id)

        logger.info(f"Executing query for group_id: {source_group_id} (type: {type(source_group_id)})")

        if not group_topics:
            logger.warning(f"[Fetching Topics] No topics found for user_id: {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ No topics are configured for this group. Please add topics and try again."
            )
            return

        # Display the topics as selectable buttons
        keyboard = [
            [InlineKeyboardButton(topic_name, callback_data=f"source_topic_{topic_id}")]
            for topic_id, topic_name in group_topics
        ]
        # Add an option for 'No specific topic'
        keyboard.append([InlineKeyboardButton("No specific topic", callback_data="source_topic_none")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text="Please select the source topic for your connection:",
            reply_markup=reply_markup,
        )

        # Update user's current step in user state
        logger.info(f"Type of `next_step`: {type(next_step)}, Value: {next_step}")
        execute_non_query(query=next_step, params=(current_step, user_id))
        logger.info(f"[CONNECTION] Updated user {user_id} current step to selecting_source_topic.")

    except Exception as e:
        logger.error(f"[Group Selection Error] Failed to select group: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An error occurred while selecting the group. Please try again."
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
    await query.answer()  # Acknowledge the callback query

    if not query.data.startswith("source_topic_") and query.data != "source_topic_none":
        raise ValueError(f"Unexpected callback data format: {query.data}")


    expected_step = SK_ADD4
    current_step = SK_ADD5
    next_step = SQL_NEXT_STEP

    user_id = query.from_user.id
    chat_id = update.effective_chat.id

    try:
        # Step Check: Verify user is in the correct workflow phase
        if not await step_checker(user_id, expected_step):
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the correct phase. Restarting the workflow..."
            )
            logger.warning(f"[STEP CHECK] User {user_id} is not in step '{expected_step}'.")
            return  # Exit early

        # Extract topic_id from callback data
        if query.data.startswith("source_topic_"):
            callback_topic_id = query.data.replace("source_topic_", "").strip()
            logger.info(f"Raw callback_topic_id: {callback_topic_id} (type: {type(callback_topic_id)})")
        elif query.data == "source_topic_none":
            callback_topic_id = "none"  # Mark none as a special case
            logger.info(f"[TARGET TOPIC] User {user_id} selected 'No specific topic'.")
        else:
            raise ValueError(f"Unexpected callback data format received: {query.data}")

        # Validate and handle the extracted topic_id
        if callback_topic_id == "none":
            logger.info(f"[VALIDATION] callback_topic_id is 'none', skipping numeric validation.")
        elif not callback_topic_id.isdigit():
            raise ValueError(f"Invalid callback topic_id (non-numeric value): {callback_topic_id}")

        # Normalize topic_id if it's numeric
        if callback_topic_id != "none":
            callback_topic_id = str(int(callback_topic_id))  # Convert to int and back to string
            logger.info(
                f"Validated and normalized callback_topic_id: {callback_topic_id} (type: {type(callback_topic_id)})")

        # Retrieve the group_id from the user's context
        group_id = context.user_data.get("source_group_id")
        if group_id is None:
            logger.error("[Topic Selection Error] No source group_id found in 'context.user_data'.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Could not determine the group you selected. Please restart the workflow."
            )
            return

        # Fetch topics associated with the group_id from the database
        fetch_topics_query = """
            SELECT topic_id, topic_name FROM group_topics
            WHERE group_id = ?;
        """
        user_topics = execute_query(fetch_topics_query, (group_id,))
        logger.info(f"Fetched topics for group_id {group_id}: {user_topics}")

        if not user_topics:  # If no topics are available for the group
            logger.warning(f"[Topic Selection] No topics found for group_id: {group_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ This group has no topics configured. Please add topics and try again. Use /help to learn how."
            )
            return

        if callback_topic_id != "none":
            matching_topic = next(
                (topic for topic in user_topics if str(topic[0]) == callback_topic_id), None
            )
            if matching_topic is None:
                logger.error(
                    f"[Topic Selection] Invalid topic_id: {callback_topic_id}, not found in group_topics for user_id: {user_id}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ The selected topic is invalid. Please try again."
                )
                return

            # Successful topic selection
            topic_id, topic_name = matching_topic  # Extract data
            logger.info(f"[Topic Selection] Matched topic_id: {topic_id}, topic_name: {topic_name}")

            connection_id = context.user_data.get("connection_id")

            # Update user_connections with the selected topic
            update_user_connection_query = """
                        UPDATE user_connections
                        SET source_topic_id = ?
                        WHERE connection_id = ?;
                    """
            execute_non_query(update_user_connection_query, (topic_id, connection_id))
            logger.info(f"[CONNECTION] Updated user {user_id} with source_topic_id {topic_id}.")

            # Notify success and proceed to the next stage
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Topic '{topic_name}' has been selected successfully as the source topic.\n"
                     f"Please continue to assign the target group."
            )
        else:
            # Special case for "none"
            logger.info(f"[Topic Selection] User {user_id} chose to not select a source topic.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ No specific topic has been selected as the source topic."
            )

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
            [InlineKeyboardButton(group_name, callback_data=f"target_group_{group_id}")]
            for group_id, group_name in user_groups
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text="Please select the target group for your connection:",
            reply_markup=reply_markup,
        )

        # Update user's current step in user_states
        try:
            logger.info(f"[STEP UPDATE] Executing query: {next_step} with params: {(current_step, user_id)}")
            execute_non_query(next_step, params=(current_step, user_id))

            # Verify the step update
            fetch_query = "SELECT current_step FROM user_states WHERE user_id = ?;"
            updated_result = execute_query(fetch_query, params=(user_id,))
            if not updated_result or updated_result[0][0] != current_step:
                logger.error(
                    f"[VERIFICATION FAILED] User {user_id} current_step update failed. "
                    f"Expected: {current_step}, Found: {updated_result}"
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Failed to update your progress. Please try again."
                )
                return
        except Exception as e:
            logger.error(
                f"[DATABASE ERROR] Failed to update/verify current_step for user {user_id}: {e}", exc_info=True
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ An error occurred while updating your progress. Please try again."
            )
            return

    except Exception as error:
        logger.error(f"[Topic Selection Error] Unexpected error for user_id {user_id}: {error}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An unexpected error occurred. Please try again or contact support."
        )

async def handle_target_group_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()  # Acknowledge the callback

    if not query.data.startswith("target_group_"):
        raise ValueError(f"Unexpected callback data format: {query.data}")

    user_id = query.from_user.id
    chat_id = query.message.chat.id
    connection_id = context.user_data.get("connection_id")
    expected_step = SK_ADD5
    current_step = SK_ADD6
    next_step = SQL_NEXT_STEP

    try:
        if not await step_checker(user_id, expected_step):
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the correct phase. Restarting the workflow."
            )
            return

        # Extract group_id from callback data
        if query.data.startswith("target_group_"):
            callback_group_id = query.data.replace("target_group_", "").strip()
        else:
            raise ValueError(f"Unexpected callback data format: {query.data}")

        # Validate that the group_id is a numeric value (supporting negative IDs, e.g., -100...)
        if not callback_group_id.lstrip('-').isdigit():  # Allow for a leading negative sign
            raise ValueError(f"Invalid callback group_id (non-numeric value): {callback_group_id}")

        try:
            # Normalize callback_group_id to an integer
            normalized_group_id = int(callback_group_id.strip())

            # Ensure callback_group_id is valid and exists in user_groups
            fetch_groups_query = """
                SELECT group_id, group_name FROM user_groups
                WHERE user_id = ?;
            """

            user_groups = execute_query(query=fetch_groups_query, params=(user_id,))
            logger.info(f"Fetched user_groups for user_id={user_id}: {user_groups}")

            logger.info(f"Executing query for group_id: {normalized_group_id} (type: {type(normalized_group_id)})")

            if not user_groups:
                logger.warning(f"[Group Selection] No groups found for user_id: {user_id}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ No groups are configured for this user. Please add groups and try again. Use /help to learn how."
                )
                return

            # Match the callback group_id to one in the user_groups
            matching_group = next((group for group in user_groups if group[0] == normalized_group_id), None)

            logger.info(f"callback_group_id: {callback_group_id}, type: {type(callback_group_id)}")
            logger.info(f"group[0] for each group in user_groups: {[group[0] for group in user_groups]}, types: {[type(group[0]) for group in user_groups]}")

            if matching_group is None:
                logger.error(
                    f"[Target Group Selection] Invalid group_id: {normalized_group_id}, not found in user_groups for user_id: {user_id}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Selected group is invalid. Please try again."
                )
                return

            target_group_id, target_group_name = matching_group
            logger.info(f"[Target Group Selection] Matched group_id: {target_group_id}, group_name: {target_group_name}")

            # Save group_id in context.user_data
            context.user_data["target_group_id"] = target_group_id
            logger.info(f"`target_group_id` stored in user_data: {context.user_data.get('target_group_id')}")

            # Update target_group_id in the database
            update_query = """
                UPDATE user_connections
                SET target_group_id = ?
                WHERE connection_id = ?;
            """

            execute_non_query(update_query, (target_group_id, connection_id))
            logger.info(f"[CONNECTION] Updated target_group_id {target_group_id} for connection_id {connection_id}.")

            # Notify user of success
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ Target group selected!",
            )

            # Prompt user to select the target topic
            target_topics = get_group_topics(target_group_id)
            if not target_topics:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=
                    "⚠️ No topics are configured for the selected group. Please select 'No specific topic' to proceed."
                )
            else:
                # Create buttons for available topics
                topic_buttons = [
                    [InlineKeyboardButton(topic_name, callback_data=f"target_topic_{topic_id}")]
                    for topic_id, topic_name in target_topics
                ]
                # Add an option for 'No specific topic'
                topic_buttons.append([InlineKeyboardButton("No specific topic", callback_data="target_topic_none")])
                reply_markup = InlineKeyboardMarkup(topic_buttons)

                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Please select the target topic for your connection:",
                    reply_markup=reply_markup,
                )

        except ValueError as e:
                logger.error(f"Failed to convert callback_group_id to integer. Received: {callback_group_id} - Error: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ An error occurred while processing the group selection. Please try again."
                )

        # Update user's current step in user_states
        try:
            logger.info(f"[STEP UPDATE] Executing query: {next_step} with params: {(current_step, user_id)}")
            execute_non_query(next_step, params=(current_step, user_id))

            # Verify the step update
            fetch_query = "SELECT current_step FROM user_states WHERE user_id = ?;"
            updated_result = execute_query(fetch_query, params=(user_id,))
            if not updated_result or updated_result[0][0] != current_step:
                logger.error(
                    f"[VERIFICATION FAILED] User {user_id} current_step update failed. "
                    f"Expected: {current_step}, Found: {updated_result}"
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Failed to update your progress. Please try again."
                )
                return
        except Exception as e:
            logger.error(
                f"[DATABASE ERROR] Failed to update/verify current_step for user {user_id}: {e}", exc_info=True
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ An error occurred while updating your progress. Please try again."
            )
            return

    except Exception as e:
        logger.error(f"[TARGET GROUP SELECTION ERROR] User {user_id} - {str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An error occurred during target group selection. Please try again or contact support."
        )

async def handle_target_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()  # Acknowledge the callback

    if not query.data.startswith("target_topic_") and query.data != "target_topic_none":
        raise ValueError(f"Unexpected callback data format: {query.data}")


    user_id = query.from_user.id
    chat_id = query.message.chat.id
    connection_id = context.user_data.get("connection_id")
    expected_step = SK_ADD6
    current_step = SK_START
    next_step = SQL_NEXT_STEP

    try:
        if not await step_checker(user_id, expected_step):
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Unexpected input. It seems you're not in the correct phase. Restarting the workflow."
            )
            return

        if query.data.startswith("target_topic_"):
            callback_topic_id = query.data.replace("target_topic_", "").strip()
            logger.info(f"Raw callback_topic_id: {callback_topic_id} (type: {type(callback_topic_id)})")
        elif query.data == "target_topic_none":
            callback_topic_id = "none"
            logger.info(f"[TARGET TOPIC] User {user_id} selected 'No specific topic'.")
        else:
            raise ValueError(f"Unexpected callback data format received: {query.data}")

        # Validate the extracted topic_id
        if callback_topic_id == "none":
            logger.info(f"[VALIDATION] callback_topic_id is 'none', skipping numeric validation.")
        elif not callback_topic_id.isdigit():
            raise ValueError(f"Invalid callback topic_id (non-numeric value): {callback_topic_id}")

        # Normalize topic_id if it's numeric
        if callback_topic_id != 'none':
            callback_topic_id = str(int(callback_topic_id))  # Convert to int and back to string
            logger.info(
                f"Validated and normalized callback_topic_id: {callback_topic_id} (type: {type(callback_topic_id)})")

        # Retrieve the group_id from the user's context
        group_id = context.user_data.get("target_group_id")
        if group_id is None:
            logger.error("[Topic Selection Error] No target group_id found in 'context.user_data'.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Could not determine the group you selected. Please restart the workflow."
            )
            return

        # Fetch topics associated with the group_id from the database
        fetch_topics_query = """
             SELECT topic_id, topic_name FROM group_topics
             WHERE group_id = ?;
         """
        user_topics = execute_query(fetch_topics_query, (group_id,))
        logger.info(f"Fetched topics for group_id {group_id}: {user_topics}")

        if not user_topics:  # If no topics are available for the group
            logger.warning(f"[Topic Selection] No topics found for group_id: {group_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ This group has no topics configured. Please add topics and try again. Use /help to learn how."
            )
            return

        # Ensure callback_topic_id matches one of the topics if not "none"
        if callback_topic_id != "none":
            matching_topic = next(
                (topic for topic in user_topics if str(topic[0]) == callback_topic_id), None
            )
            if matching_topic is None:
                logger.error(
                    f"[Topic Selection] Invalid topic_id: {callback_topic_id}, not found in group_topics for user_id: {user_id}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ The selected topic is invalid. Please try again."
                )
                return

            # Successful topic selection
            topic_id, topic_name = matching_topic  # Extract data
            logger.info(f"[Topic Selection] Matched topic_id: {topic_id}, topic_name: {topic_name}")

            # Update the selected `target_topic_id` in the database
            update_query = """
                 UPDATE user_connections
                 SET target_topic_id = ?
                 WHERE connection_id = ?;
             """
            execute_non_query(update_query, (topic_id, connection_id))
            logger.info(f"[CONNECTION] Updated target_topic_id {topic_id} for connection_id {connection_id}.")

            # Save target_topic_id in context.user_data
            context.user_data["target_topic_id"] = topic_id
            logger.info(f"`target_topic_id` stored in user_data: {context.user_data.get('target_topic_id')}")

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ You can now create another connection or return to the main menu.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Return to Main Menu", callback_data="main_menu")]
                ])
            )
        else:
            # Special case for "none"
            logger.info(f"[Topic Selection] User {user_id} chose to not select a source topic.")
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ No specific topic has been selected for the target topic."
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ You can now create another connection or return to the main menu.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Return to Main Menu", callback_data="main_menu")]
                ])
            )

        # Update user's current step in user_states
        try:
            logger.info(f"[STEP UPDATE] Executing query: {next_step} with params: {(current_step, user_id)}")
            execute_non_query(next_step, params=(current_step, user_id))

            # Verify the step update
            fetch_query = "SELECT current_step FROM user_states WHERE user_id = ?;"
            updated_result = execute_query(fetch_query, params=(user_id,))
            if not updated_result or updated_result[0][0] != current_step:
                logger.error(
                    f"[VERIFICATION FAILED] User {user_id} current_step update failed. "
                    f"Expected: {current_step}, Found: {updated_result}"
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Failed to update your progress. Please try again."
                )
                return

        except Exception as e:
            logger.error(
                f"[DATABASE ERROR] Failed to update/verify current_step for user {user_id}: {e}", exc_info=True
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ An error occurred while updating your progress. Please try again."
            )
            return

    except Exception as e:
        logger.error(f"[TARGET TOPIC SELECTION ERROR] User {user_id} - {str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An error occurred during target topic selection. Please try again or contact support."
        )