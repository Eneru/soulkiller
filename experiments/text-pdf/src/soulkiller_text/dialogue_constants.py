"""Reviewed synthetic-answer bounds and explicit profile identity."""

DIALOGUE_CORPUS = "experiments/text-pdf/examples/persona-inez"
PERSONA_ID = "inez"
PERSONA_LABEL = "Inez (invented)"
MAX_QUESTION_CODE_POINTS = 500
MAX_ANSWER_CODE_POINTS = 2000
MAX_COMPLETION_BYTES = 64 * 1024
DEMO_BACKEND = "scripted_demo"
NO_BACKEND = "not_called"
PROFILE_SOURCES: dict[str, tuple[str, str, str]] = {
    "inez-fr": ("8a9a071ff9f400c5e41c5b449dce7969717e7485ef5a6a9de05868e63d6cd7a8", "Inez", "Inez"),
    "inez-en": ("2fb2d961ff6e6ac7f93c78882c74d3477d9914760f4a92f9286f64e9f97f96fb", "Inez", "Inez"),
    "shared-letter": (
        "f488ed07ea7225e263f4d471b4c6740c1270a52131f34079afcd502fc196c3c3",
        "Corin",
        "Corin",
    ),
    "archived-instruction": (
        "201ea4d7b5a9fe5e63c2b6417f6355ce6d9e9140cb6caee50b7c1f4bc6408124",
        "Archive author",
        "Inez",
    ),
}
