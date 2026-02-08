#!/usr/bin/env python3
"""
Partition tasks from tasks.md into groups for parallel implementation.

Groups tasks by file ownership using connected-component analysis:
tasks that share any target file are placed in the same group.

Usage:
    python partition_tasks.py <tasks-md-path> [--max-groups 3]

Output (JSON to stdout):
    {
      "parallelizable": true,
      "groups": [
        {
          "id": 1,
          "tasks": ["Task 1 description", "Task 3 description"],
          "files": ["src/auth.ts", "src/middleware.ts"]
        },
        ...
      ],
      "ungrouped": ["Task with no files mentioned"]
    }
"""

import argparse
import json
import re
import sys
from collections import defaultdict


def parse_tasks(content: str) -> list:
    """Parse tasks.md into structured task objects.

    Looks for task patterns like:
    - ## Task 1: Description
    - ### Task 1: Description
    - **Task 1:** Description
    - - [ ] Task description

    Extracts file references from each task section.
    """
    tasks = []
    current_task = None
    current_body = []

    for line in content.split("\n"):
        # Match task headers
        task_match = re.match(
            r'^#{2,3}\s+(?:Task\s+\d+[:.]\s*)?(.+)$', line
        )
        bold_match = re.match(
            r'^\*\*(?:Task\s+\d+[:.]\s*)?(.+?)\*\*', line
        )
        checkbox_match = re.match(
            r'^[-*]\s+\[[ x]\]\s+(.+)$', line, re.IGNORECASE
        )

        match = task_match or bold_match or checkbox_match
        if match:
            if current_task:
                tasks.append({
                    "title": current_task,
                    "body": "\n".join(current_body),
                    "files": extract_files("\n".join(current_body)),
                })
            current_task = match.group(1).strip()
            current_body = [line]
        elif current_task:
            current_body.append(line)

    # Don't forget the last task
    if current_task:
        tasks.append({
            "title": current_task,
            "body": "\n".join(current_body),
            "files": extract_files("\n".join(current_body)),
        })

    return tasks


def extract_files(text: str) -> list:
    """Extract file paths from task body text.

    Looks for patterns like:
    - `src/auth.ts`
    - src/auth.ts (bare paths with extensions)
    - **File:** src/auth.ts
    """
    files = set()

    # Backtick-quoted paths
    for match in re.finditer(r'`([^`]+\.[a-zA-Z]{1,10})`', text):
        path = match.group(1)
        if _looks_like_file(path):
            files.add(path)

    # Bare paths with common extensions
    for match in re.finditer(
        r'(?:^|\s)((?:[\w./\-]+/)?[\w.\-]+\.(?:ts|tsx|js|jsx|py|rb|go|rs|java|sql|css|scss|html|vue|svelte))\b',
        text
    ):
        path = match.group(1)
        if _looks_like_file(path):
            files.add(path)

    return sorted(files)


def _looks_like_file(path: str) -> bool:
    """Heuristic: does this string look like a file path?"""
    if not path or len(path) > 200:
        return False
    if path.startswith("http://") or path.startswith("https://"):
        return False
    if " " in path:
        return False
    # Must have an extension
    if "." not in path.split("/")[-1]:
        return False
    return True


def build_file_graph(tasks: list) -> dict:
    """Build a mapping from file -> set of task indices."""
    file_to_tasks = defaultdict(set)
    for i, task in enumerate(tasks):
        for f in task["files"]:
            file_to_tasks[f].add(i)
    return file_to_tasks


def find_connected_components(tasks: list, file_to_tasks: dict) -> list:
    """Find connected components of tasks via shared files."""
    n = len(tasks)
    visited = [False] * n
    components = []

    def dfs(node, component):
        visited[node] = True
        component.add(node)
        for f in tasks[node]["files"]:
            for neighbor in file_to_tasks[f]:
                if not visited[neighbor]:
                    dfs(neighbor, component)

    for i in range(n):
        if not visited[i] and tasks[i]["files"]:
            component = set()
            dfs(i, component)
            components.append(component)

    return components


def partition(tasks: list, max_groups: int = 3) -> dict:
    """Partition tasks into groups for parallel execution."""
    file_to_tasks = build_file_graph(tasks)
    components = find_connected_components(tasks, file_to_tasks)

    # Tasks with no file references
    tasks_with_files = set()
    for comp in components:
        tasks_with_files.update(comp)

    ungrouped = [
        tasks[i]["title"] for i in range(len(tasks))
        if i not in tasks_with_files
    ]

    # If everything is one component, not parallelizable
    if len(components) <= 1 and not ungrouped:
        all_files = sorted(set(f for t in tasks for f in t["files"]))
        return {
            "parallelizable": False,
            "groups": [{
                "id": 1,
                "tasks": [t["title"] for t in tasks],
                "files": all_files,
            }],
            "ungrouped": [],
        }

    # Sort components by size (largest first) and merge if over max_groups
    components.sort(key=len, reverse=True)

    while len(components) > max_groups:
        # Merge the two smallest
        smallest = components.pop()
        second_smallest = components.pop()
        components.append(smallest | second_smallest)
        components.sort(key=len, reverse=True)

    groups = []
    for idx, comp in enumerate(components, 1):
        task_titles = [tasks[i]["title"] for i in sorted(comp)]
        files = sorted(set(f for i in comp for f in tasks[i]["files"]))
        groups.append({
            "id": idx,
            "tasks": task_titles,
            "files": files,
        })

    return {
        "parallelizable": len(groups) > 1 or bool(ungrouped),
        "groups": groups,
        "ungrouped": ungrouped,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Partition tasks.md into groups for parallel implementation"
    )
    parser.add_argument("tasks_file", help="Path to tasks.md")
    parser.add_argument(
        "--max-groups", type=int, default=3,
        help="Maximum number of task groups (default: 3)"
    )

    args = parser.parse_args()

    try:
        with open(args.tasks_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {args.tasks_file} not found", file=sys.stderr)
        sys.exit(1)

    tasks = parse_tasks(content)

    if not tasks:
        print(json.dumps({
            "parallelizable": False,
            "groups": [],
            "ungrouped": [],
            "error": "No tasks found in file",
        }, indent=2))
        sys.exit(0)

    result = partition(tasks, max_groups=args.max_groups)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
