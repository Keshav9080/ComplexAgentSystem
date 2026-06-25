"""CLI demo — task decomposition pipeline."""

from decomposer import TaskDecomposer


def main() -> None:
    decomposer = TaskDecomposer()

    examples = [
        "Fetch 10 papers, extract key points, and generate a report.",
        "Fetch the latest sales report, analyze trends, and write an executive summary.",
        "Retrieve customer feedback. Then summarize key themes and generate a response draft.",
    ]

    for request in examples:
        plan = decomposer.decompose(request)
        print(f"Request: {plan.original_request}\n")

        print("  Subtasks:")
        for index, subtask in enumerate(plan.subtasks, start=1):
            print(f"    {index}. {subtask.description}")

        print("\n  Assigned steps:")
        for step in plan.steps:
            keywords = ", ".join(step.matched_keywords) or "default"
            print(
                f"    {step.order}. [{step.agent.value}] "
                f"({keywords}) -> {step.description}"
            )
        print()


if __name__ == "__main__":
    main()
