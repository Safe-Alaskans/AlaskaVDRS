import os

from dotenv import load_dotenv

from model_tuning_workspace.synthetic_data_pipeline.storage.mongo_storage import MongoDBHandler

if __name__ == "__main__":
    load_dotenv()
    db_handler = MongoDBHandler(
        connection_string=os.getenv('MONGO_CONNECTION_STRING'),
        database_name=os.getenv('MONGO_DB_NAME')
    )

    all_dps = db_handler.get_all_documents(collection_name="synthetic_data")

    ids_to_delete = []
    for dp in all_dps:
        output: str = dp.get('edited_teacher_output')
        if output and output.lower().strip() == 'delete':
            print(f"Document with id: {dp['_id']} has an edited_teacher_output. Adding to list for deletion.")
            ids_to_delete.append(dp['_id'])


    total_num_deletions =0
    for id_to_del in ids_to_delete:
        print(f"Deleting document with id: {id_to_del}")
        num_deleted = db_handler.delete_document(collection_name="synthetic_data", document_id=id_to_del)
        total_num_deletions += num_deleted

    print(f"Total number of documents deleted: {total_num_deletions}")
