"""
Stage 5 interface: a Gradio web app over the grounded RAG loop.

Thin shell around generate.answer(). It takes a typed question, runs
retrieve -> ground -> generate, and shows two fields:
  - Answer: the grounded reply (the model also cites passage numbers inline), and
  - Retrieved from: the source documents, appended in code from retrieval
    metadata (generate.format_sources) so attribution is guaranteed, not left
    to the model. On a refusal (out-of-domain / not in the docs) this box says
    so, because no source backed the answer.

Run:  .venv/bin/python app.py    then open http://localhost:7860
"""

import gradio as gr

from generate import answer

TITLE = "The Unofficial Guide — NRP Nautilus Cluster"
DESCRIPTION = (
    "Ask about access, GPUs, batch jobs, storage, policies, and troubleshooting "
    "on the NRP Nautilus cluster (https://nrp.ai). Answers are grounded in the "
    "official NRP user docs and cite their sources — if the docs don't cover it, "
    "the guide says so rather than guessing."
)

EXAMPLES = [
    "As a student, how do I get access to the NRP Nautilus cluster?",
    "Why did the data in my pod disappear after it restarted, and how do I prevent it?",
    "How do I request a GPU for my pod?",
    "What happens if I run a job with a sleep command that never ends?",
    "What types of data am I not allowed to store on NRP?",
]


def _format_sources(sources: list[dict]) -> str:
    """Render the code-built source list as plain text for the 'Retrieved from' box."""
    lines = []
    for s in sources:
        secs = "; ".join(s["sections"])
        lines.append(f"[{s['n']}] {s['doc']} — {secs}\n    {s['source_url']}")
    return "\n".join(lines)


def handle_query(question: str):
    """question -> (answer text, 'Retrieved from' text)."""
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""

    result = answer(question)

    if result["refused"] or not result["sources"]:
        # Refusal: be explicit that nothing was retrieved to back an answer.
        return result["answer"], "(no sources — the docs don't cover this question)"

    return result["answer"], _format_sources(result["sources"])


def build_app() -> gr.Blocks:
    with gr.Blocks(title=TITLE) as demo:
        gr.Markdown(f"# {TITLE}")
        gr.Markdown(DESCRIPTION)

        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. How do I request a GPU for my pod?",
            lines=2,
            autofocus=True,
        )
        btn = gr.Button("Ask", variant="primary")

        answer_box = gr.Textbox(label="Answer", lines=8)
        sources_box = gr.Textbox(label="Retrieved from", lines=4)

        gr.Examples(examples=EXAMPLES, inputs=inp, label="Try one of the eval questions")

        # Button click and Enter-to-submit both run the grounded RAG loop.
        btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
        inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])

    return demo


if __name__ == "__main__":
    build_app().launch()
