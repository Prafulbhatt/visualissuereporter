"""The logging agent.

Once the person confirms a description, this module builds a tiny LangChain
agent whose only job is to pick the best category and call the `log_issue`
tool exactly once. The tool call is what actually inserts the row into
SQLite — the photo path is bound in from the app code (not typed by the
model) so the file reference is always correct.
"""
import os
from datetime import datetime

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq

import db

AGENT_MODEL = os.getenv("GROQ_AGENT_MODEL", "openai/gpt-oss-120b")

CATEGORY_LIST = ", ".join(db.CATEGORIES)

SYSTEM_PROMPT = (
    "You are a backend logging agent for a facility/equipment issue tracker. "
    "You will be given a description that a person has already confirmed as "
    "accurate. Your only job is to choose the single best-fitting category "
    f"from this exact list: {CATEGORY_LIST}. Then call the log_issue tool "
    "exactly once with that category and the description. Do not call it "
    "more than once, and do not ask the user anything else. After the tool "
    "call succeeds, reply with one short confirmation sentence."
)


def make_log_issue_tool(photo_path: str):
    """Build a log_issue tool bound to a specific photo path.

    Binding photo_path here (rather than having the model produce it) keeps
    the file reference deterministic — the agent only ever reasons about
    the category, never the filesystem.
    """

    @tool
    def log_issue(description: str, category: str) -> str:
        """Log a confirmed physical issue report into the tracking database.

        Call this exactly once, only for a description the reporter has
        already confirmed as accurate.

        Args:
            description: The confirmed, human-readable description of the issue.
            category: One category label, chosen from the allowed list given
                in your instructions.
        """
        if category not in db.CATEGORIES:
            category = "Other"
        timestamp = datetime.now().isoformat(timespec="seconds")
        issue_id = db.insert_issue(
            description=description,
            category=category,
            photo_path=photo_path,
            timestamp=timestamp,
        )
        return f"Issue #{issue_id} logged under '{category}' at {timestamp}."

    return log_issue


def run_logging_agent(confirmed_description: str, photo_path: str) -> str:
    """Invoke the agent on a confirmed description. Returns its final reply."""
    log_issue_tool = make_log_issue_tool(photo_path)
    llm = ChatGroq(model=AGENT_MODEL, temperature=0)
    agent = create_agent(llm, tools=[log_issue_tool], system_prompt=SYSTEM_PROMPT)

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f'Confirmed issue description: "{confirmed_description}"',
                }
            ]
        }
    )

    messages = result.get("messages", [])
    if not messages:
        return "Issue logged."
    final = messages[-1]
    content = getattr(final, "content", None)
    return content.strip() if content else "Issue logged."