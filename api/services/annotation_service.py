from db.connect import connect, commit_and_close
from psycopg2 import sql

def delete_unlabeled_row(id_):
    conn, cur = connect()
    try:
        delete_query = sql.SQL(
            "DELETE FROM unlabeled.data WHERE id = %s"
        )
        cur.execute(delete_query, (id_,))
        
        commit_and_close(conn, cur)
        print(f"Row with id {id_} deleted successfully")
    except Exception as e:
        print(f"Error deleting row with id {id_}: {e}")
        if conn:
            conn.rollback()
        commit_and_close(conn, cur)
        raise