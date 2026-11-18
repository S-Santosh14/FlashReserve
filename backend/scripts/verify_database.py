from backend.database.mongodb import mongodb
from backend.database.raft_database import (
    close_raft_connections,
    get_raft_database,
)
from backend.config import settings


def verify_database():

    try:

        print("\n========== FLASHRESERVE DATABASE TEST ==========\n")

        main_db = mongodb.connect()

        print("\nMAIN DATABASE")
        print("------------------------------")

        collections = sorted(
            main_db.list_collection_names()
        )

        print(f"Database: {main_db.name}")

        for collection in collections:

            print(f"  [OK] {collection}")

        print("\nRAFT DATABASES")
        print("------------------------------")

        for node_id in settings.raft_nodes():
            database = get_raft_database(node_id)

            print(f"\n{node_id}: {database.name}")

            node_collections = sorted(
                database.list_collection_names()
            )

            for collection in node_collections:

                print(f"  [OK] {collection}")

        print("\n==============================================")
        print("DATABASE VERIFICATION COMPLETED")
        print("==============================================")

    except Exception as error:

        print(f"\nDatabase verification failed: {error}")

        raise

    finally:
        close_raft_connections()
        mongodb.close()


if __name__ == "__main__":

    verify_database()