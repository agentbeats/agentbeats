from datasets import load_dataset
import logging

logger = logging.getLogger(__name__)

INSTANCE_ID = "gpac.cve-2023-5586"

HUGGINGFACE_DATASET_NAME = "SEC-bench/SEC-bench"


def get_workspace_dir_name(instance_id: str) -> str:
    """
    Get the workspace directory name for a given instance ID from the SEC-bench dataset.

    Parameters:
    - instance_id: The unique identifier for the instance in the dataset
    """
    try:
        # Load the SEC-bench dataset
        dataset = load_dataset(HUGGINGFACE_DATASET_NAME, split="eval")

        logger.info(
            f"[get_workspace_dir_name] Loaded dataset: {dataset}. Instance ID: {instance_id}"
        )

        # Find the instance with matching ID
        for instance in dataset:
            if instance["instance_id"] == instance_id:
                return instance["work_dir"]

        return f"Error: No instance found with ID {instance_id}"
    except Exception as e:
        error_msg = f"Error getting workspace directory name: {e}"
        logger.error(error_msg)
        return error_msg


def get_sanitizer_report(instance_id: str) -> str:
    """
    Get the sanitizer report for a given instance ID from the SEC-bench dataset.

    Parameters:
    - instance_id: The unique identifier for the instance in the dataset
    """
    try:
        # Load the SEC-bench dataset
        dataset = load_dataset(HUGGINGFACE_DATASET_NAME, split="eval")

        # Find the instance with matching ID
        for instance in dataset:
            if instance["instance_id"] == instance_id:
                logger.info(
                    f"[get_sanitizer_report] Brief sanitizer report: {instance['sanitizer_report'][:100]}"
                )
                return instance["sanitizer_report"]

        return f"Error: No instance found with ID {instance_id}"
    except Exception as e:
        error_msg = f"Error getting sanitizer report: {e}"
        logger.error(error_msg)
        return error_msg


def get_bug_report(instance_id: str) -> str:
    """
    Get the bug report for a given instance ID from the SEC-bench dataset.

    Parameters:
    - instance_id: The unique identifier for the instance in the dataset
    """
    try:
        # Load the SEC-bench dataset
        dataset = load_dataset(HUGGINGFACE_DATASET_NAME, split="eval")

        logger.info(
            f"[get_bug_report] Loaded dataset: {dataset}. Instance ID: {instance_id}"
        )

        # Find the instance with matching ID
        for instance in dataset:
            if instance["instance_id"] == instance_id:
                logger.info(
                    f"Brief bug report: {instance['bug_report'][:100]}"
                )
                return instance["bug_report"]

        return f"Error: No instance found with ID {instance_id}"
    except Exception as e:
        error_msg = f"Error getting bug report: {e}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    print(get_workspace_dir_name(INSTANCE_ID))
    print(get_sanitizer_report(INSTANCE_ID))
    print(get_bug_report(INSTANCE_ID))
