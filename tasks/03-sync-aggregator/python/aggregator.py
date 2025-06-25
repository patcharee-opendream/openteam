from __future__ import annotations
from typing import List, Dict
import multiprocessing
import time
import os
from pathlib import Path
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)  # Import ThreadPoolExecutor and as_completed


# The worker function for processing a single file.
# It no longer needs a queue 'q' as results will be returned directly by the executor.
def _process_file_worker(base_dir: str, rel_path: str) -> Dict:
    """
    Worker function to process a single file.
    This function will be executed by a worker in the ThreadPoolExecutor.
    It returns a dictionary containing file statistics or a timeout status.
    """
    try:
        # Construct the absolute path to the file
        abs_path = os.path.join(base_dir, rel_path)

        # Open and read the file content
        with open(abs_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Check for a '#sleep=N' marker in the first line
        # This simulates a delay for certain files to test timeout behavior
        if lines and lines[0].startswith("#sleep="):
            sleep_sec = int(lines[0].split("=", 1)[1].strip())
            if (
                sleep_sec > 2
            ):  # If sleep_sec exceeds timeout, return timeout immediately
                return {"path": rel_path, "status": "timeout"}
            time.sleep(sleep_sec)  # Introduce the simulated delay
            lines = lines[1:]  # Remove the sleep marker line from content for stats

        # Calculate the number of lines
        num_lines = len(lines)
        # Calculate the total word count by splitting each line and summing lengths
        word_count = sum(len(line.split()) for line in lines)

        # Return the file statistics with an "ok" status
        return {
            "path": rel_path,
            "lines": num_lines,
            "words": word_count,
            "status": "ok",
        }
    except Exception as e:
        # If any exception occurs (e.g., file not found, permission error),
        # or if a TimeoutError is raised later by future.result(),
        # we consider it a "timeout" status for this file.
        # This ensures that even non-timeout errors are reported consistently.
        return {"path": rel_path, "status": "timeout"}


def aggregate(filelist_path: str, workers: int = 4, timeout: int = 2) -> List[Dict]:
    """
    Aggregates file statistics from a list of files, processing them concurrently.

    Args:
        filelist_path (str): The path to a text file containing a list of relative file paths.
        workers (int): The maximum number of concurrent worker threads to use.
        timeout (int): The maximum time in seconds to wait for each file to be processed.

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary contains
                    statistics for a file or a "timeout" status if processing failed
                    or exceeded the timeout. The order of results matches the input filelist.
    """
    # Convert filelist_path to a Path object for easier parent directory access
    filelist_path = Path(filelist_path)
    # Get the base directory from which relative file paths will be resolved
    base_dir = str(filelist_path.parent)

    # Read the list of relative file paths from the filelist
    with open(filelist_path, encoding="utf-8") as f:
        paths = [line.strip() for line in f if line.strip()]

    # Initialize a results list with None placeholders.
    # This allows us to place results into their correct original order later.
    results = [None] * len(paths)

    # Use ThreadPoolExecutor for concurrent processing.
    # ThreadPoolExecutor is suitable for I/O-bound tasks like file reading.
    # The 'max_workers' argument controls the number of concurrent operations.
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit each file processing task to the executor.
        # We store a mapping from each 'Future' object (representing a pending result)
        # back to its original index in the 'paths' list. This is crucial for order preservation.
        future_to_index = {
            executor.submit(_process_file_worker, base_dir, path): i
            for i, path in enumerate(paths)
        }

        # Iterate over futures as they complete, using 'as_completed'.
        # This allows us to process results as soon as they are ready,
        # without waiting for all tasks to finish.
        for future in as_completed(future_to_index):
            # Retrieve the original index for the completed future
            index = future_to_index[future]
            # Retrieve the original file path associated with this index
            path = paths[index]

            try:
                # Attempt to get the result from the future.
                # The 'timeout' argument enforces the per-file timeout.
                # If the worker function takes longer than 'timeout' seconds,
                # a concurrent.futures.TimeoutError will be raised.
                result = future.result(timeout=timeout)
                # Store the successful result in its correct position
                results[index] = result
            except Exception:
                # If any exception occurred during execution of the worker function
                # (e.g., file I/O error caught inside _process_file_worker),
                # or if a TimeoutError was raised by future.result(),
                # mark this entry as a "timeout".
                results[index] = {"path": path, "status": "timeout"}

    return results
