from agnocli.workflows import register_workflow

@register_workflow(name="hello", description="Hello workflow returning markdown")
def hello(name: str = "world") -> str:
    return (
        f"# Hello, {name}!\n\n"
        "This is **Markdown** with a table and ANSI colors.\n\n"
        "| Col | Val |\n|-----|-----|\n| A   | 1   |\n| B   | 2   |\n"
    )


@register_workflow(name="sum", description="Sum two integers")
def sum_numbers(a: int = 1, b: int = 2) -> str:
    s = int(a) + int(b)
    return f"Result: {a} + {b} = {s}"
