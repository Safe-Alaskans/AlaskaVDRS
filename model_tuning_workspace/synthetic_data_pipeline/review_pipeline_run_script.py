import os
import tempfile
import subprocess

from dotenv import load_dotenv

from model_tuning_workspace.synthetic_data_pipeline.storage.mongo_storage import MongoDBHandler

COLLECTION_NAME = "synthetic_data"


def edit_in_editor(initial_content: str) -> tuple[str, bool]:
    """Open text in a temporary file with TextEdit and wait for user confirmation.
    Returns tuple of (edited_content, should_delete)"""
    with tempfile.NamedTemporaryFile(suffix=".txt", mode='w', delete=False) as tf:
        tf.write(initial_content)
        temp_filename = tf.name

    try:
        subprocess.call(['open', '-a', 'TextEdit', temp_filename])

        while True:
            response = input("\nHave you finished editing? (y/n/d to delete): ").lower()
            if response == 'y':
                break
            elif response == 'n':
                print("Please finish editing in TextEdit and then enter 'y'")
            elif response == 'd':
                return initial_content, True
            else:
                print("Please enter 'y' when done, 'n' if still editing, or 'd' to delete")

        with open(temp_filename, 'r') as tf:
            edited_content = tf.read()

        return edited_content, False
    finally:
        os.unlink(temp_filename)


def review_teacher_outputs(pipeline_run_id: str, db_handler: MongoDBHandler):
    """Review and optionally edit teacher outputs for a specific pipeline run."""
    query = {"pipeline_run_id": pipeline_run_id}
    total_docs = db_handler.count_documents(COLLECTION_NAME, query)
    print(f"Found {total_docs} documents for pipeline run {pipeline_run_id}")

    documents = db_handler.find_documents(COLLECTION_NAME, query)

    for i, doc in enumerate(documents, 1):
        print(f"\nReviewing document {i} of {total_docs}")
        print(f"Iteration ID: {doc.get('iteration_id', 'N/A')}")

        teacher_output = doc["outputs"].get("teacher_model_gen")
        if not teacher_output:
            print("No teacher output found in this document. Skipping...")
            continue

        print("\nCurrent teacher output:")
        print("-" * 80)
        print(teacher_output)
        print("-" * 80)

        while True:
            choice = input("\nWould you like to (e)dit, (d)elete, (s)kip, or (q)uit? ").lower()

            if choice == 'q':
                print("Exiting review process...")
                return
            elif choice == 's':
                print("Skipping to next document...")
                break
            elif choice == 'd':
                confirm = input("Are you sure you want to delete this document? (y/n): ").lower()
                if confirm == 'y':
                    db_handler.delete_document(COLLECTION_NAME, doc["_id"])
                    print("Document deleted successfully")
                    break
                else:
                    print("Deletion cancelled")
            elif choice == 'e':
                edited_output, should_delete = edit_in_editor(teacher_output)

                if should_delete:
                    confirm = input("Are you sure you want to delete this document? (y/n): ").lower()
                    if confirm == 'y':
                        db_handler.delete_document(COLLECTION_NAME, doc["_id"])
                        print("Document deleted successfully")
                    else:
                        print("Deletion cancelled")
                elif edited_output != teacher_output:
                    update_query = {
                        "pipeline_run_id": pipeline_run_id,
                        "iteration_id": doc.get("iteration_id")
                    }
                    update = {
                        "$set": {"edited_teacher_output": edited_output}
                    }
                    db_handler.update_document_by_query(
                        collection_name=COLLECTION_NAME,
                        query=update_query,
                        update=update
                    )
                    print("Successfully updated document with edited content")
                else:
                    print("No changes detected")
                break
            else:
                print("Invalid choice. Please enter 'e' to edit, 'd' to delete, 's' to skip, or 'q' to quit.")


if __name__ == "__main__":
    load_dotenv()

    # Initialize the MongoDB handler
    db_handler = MongoDBHandler(
        connection_string=os.getenv('MONGO_CONNECTION_STRING'),
        database_name=os.getenv('MONGO_DB_NAME')
    )

    try:
        review_teacher_outputs(
            pipeline_run_id="52e9f1e3-7e19-46eb-b2e3-9643e893c136",
            db_handler=db_handler
        )
    finally:
        # Ensure we close the connection when done
        db_handler.close_connection()
