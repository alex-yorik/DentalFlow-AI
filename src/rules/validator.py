from src.config.loader import RulesConfig
from src.llm.contracts import AIOutput, SuggestedAction


class ValidationResult:
    def __init__(self, valid: bool, ai_output: AIOutput, reason: str | None = None):
        self.valid = valid
        self.ai_output = ai_output
        self.reason = reason


def validate_ai_output(output: AIOutput, rules: RulesConfig) -> ValidationResult:
    if output.confidence < rules.confidence_threshold:
        return ValidationResult(
            valid=False,
            ai_output=output,
            reason=f"confidence {output.confidence:.2f} < threshold {rules.confidence_threshold}",
        )

    if output.is_lead and output.suggested_action in (
        SuggestedAction.CLOSE, SuggestedAction.ANSWER_FAQ,
    ):
        return ValidationResult(
            valid=False,
            ai_output=output,
            reason=f"is_lead=True but suggested_action={output.suggested_action.value}",
        )

    if not output.is_lead and output.suggested_action in (
        SuggestedAction.QUALIFY, SuggestedAction.CRM_WRITE,
    ):
        return ValidationResult(
            valid=False,
            ai_output=output,
            reason=f"is_lead=False but suggested_action={output.suggested_action.value}",
        )

    if output.intent.name == "UNSAFE" and output.safe:
        return ValidationResult(
            valid=False,
            ai_output=output,
            reason="intent=unsafe but safe=True — inconsistent",
        )

    return ValidationResult(valid=True, ai_output=output)
