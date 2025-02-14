import sqlite3
from typing import Sequence, Any
from GLOSSARY import logger, DB_FILE

#### ------- [ QUERY EXECUTION HELPERS ] ------- ####

def log_and_handle_query_error(query: str, error: Exception):
    logger.error(f"Query execution failed: '{query}' | Error: {error}")
    return 0  # Always return 0 in case of errors for consistency.

def execute_non_query(query: str = '', params: Sequence = ()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        logger.info(f"[DATABASE] Executing non-query: {query} | Params: {params}")
        cursor.execute(query, params)  # Run the provided query with params
        conn.commit()
        logger.info(f"[DATABASE] Data inserted / updated successfully.: {params}")
    except Exception as error:
        return log_and_handle_query_error(query, error)
    finally:
        conn.close()

def execute_query(query: str, params: Sequence = (), fetch: bool = True):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        logger.info(f"[DATABASE] Executing query:\n"
                    f"{query}\n"
                    f"Params: {params}")

        cursor.execute(query, params)

        logger.info(f"[DATABASE] Query Executed Successfully")

        if fetch:
            return cursor.fetchall()  # Fetch results if requested
    except Exception as err:
        return log_and_handle_query_error(query, err)
    finally:
        conn.close()
    return []  # Return an empty list by default
