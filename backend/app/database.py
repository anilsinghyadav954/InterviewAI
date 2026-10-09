from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import OperationFailure
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize client
client: MongoClient = None
db: Database = None


def get_client() -> MongoClient:
    global client
    if client is None:
        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return client


def get_database() -> Database:
    global db
    if db is None:
        c = get_client()
        db = c[settings.DATABASE_NAME]
    return db


def get_users_collection() -> Collection:
    database = get_database()
    return database["users"]


def get_resume_analyses_collection() -> Collection:
    database = get_database()
    return database["resume_analyses"]


def get_interview_question_sets_collection() -> Collection:
    database = get_database()
    return database["interview_question_sets"]


def get_interview_evaluations_collection() -> Collection:
    database = get_database()
    return database["interview_answer_evaluations"]


def get_voice_sessions_collection() -> Collection:
    database = get_database()
    return database["voice_interview_sessions"]


def get_password_resets_collection() -> Collection:
    database = get_database()
    return database["password_reset_tokens"]


def init_db():
    """Initializes indexes and ensures database connectivity."""
    try:
        users = get_users_collection()
        # Ensure unique index on normalized email
        existing_indexes = users.index_information()
        if "email_1" not in existing_indexes and "unique_email_idx" not in existing_indexes:
            users.create_index([("email", ASCENDING)], unique=True)
            logger.info("Created unique email index on users collection.")
        else:
            logger.info("Unique email index verified on users collection.")

        # Ensure index on resume_analyses for user_id and created_at
        resumes = get_resume_analyses_collection()
        resume_indexes = resumes.index_information()
        if "user_id_1_created_at_-1" not in resume_indexes:
            resumes.create_index([("user_id", ASCENDING), ("created_at", -1)])
            logger.info("Created user_id and created_at index on resume_analyses.")

        # Ensure index on interview_question_sets for user_id and created_at
        qsets = get_interview_question_sets_collection()
        qset_indexes = qsets.index_information()
        if "user_id_1_created_at_-1" not in qset_indexes:
            qsets.create_index([("user_id", ASCENDING), ("created_at", -1)])
            logger.info("Created user_id and created_at index on interview_question_sets.")
        if "user_id_1_interview_type_1" not in qset_indexes:
            qsets.create_index([("user_id", ASCENDING), ("interview_type", ASCENDING)])
        if "user_id_1_target_role_1" not in qset_indexes:
            qsets.create_index([("user_id", ASCENDING), ("target_role", ASCENDING)])

        # Ensure indexes on interview_answer_evaluations
        evals = get_interview_evaluations_collection()
        eval_indexes = evals.index_information()
        if "question_set_id_1_question_number_1" not in eval_indexes:
            evals.create_index([("question_set_id", ASCENDING), ("question_number", ASCENDING)], unique=True)
            logger.info("Created unique compound index on interview_answer_evaluations (question_set_id, question_number).")
        if "user_id_1_created_at_-1" not in eval_indexes:
            evals.create_index([("user_id", ASCENDING), ("created_at", -1)])
            logger.info("Created user_id and created_at index on interview_answer_evaluations.")

        # Ensure indexes on voice_interview_sessions
        voice_col = get_voice_sessions_collection()
        voice_indexes = voice_col.index_information()
        if "user_id_1_started_at_-1" not in voice_indexes:
            voice_col.create_index([("user_id", ASCENDING), ("started_at", -1)])
        if "user_id_1_status_1" not in voice_indexes:
            voice_col.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
        if "question_set_id_1" not in voice_indexes:
            voice_col.create_index([("question_set_id", ASCENDING)])
        logger.info("Verified indexes on voice_interview_sessions.")

        # Ensure indexes on password_reset_tokens
        resets_col = get_password_resets_collection()
        reset_indexes = resets_col.index_information()
        if "token_hash_1" not in reset_indexes:
            resets_col.create_index([("token_hash", ASCENDING)])
        if "user_id_1_created_at_-1" not in reset_indexes:
            resets_col.create_index([("user_id", ASCENDING), ("created_at", -1)])
        if "email_1" not in reset_indexes:
            resets_col.create_index([("email", ASCENDING)])
        if "expires_at_1" not in reset_indexes:
            resets_col.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
        logger.info("Verified indexes on password_reset_tokens.")

        logger.info(f"Connected to MongoDB '{settings.DATABASE_NAME}'.")
    except OperationFailure as e:
        logger.warning(f"Index check/creation notice: {e}")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise e


def close_db_connection():
    global client
    if client:
        client.close()
        client = None
