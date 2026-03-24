from ai_agent.backend.service import AiAgentService


def test_message_template_query_includes_image_fields():
    config = AiAgentService._default_query_parts("message_template")

    assert config is not None
    assert "image_url" in config["select"]
    assert "attachment_id" in config["select"]
    assert "file_path" in config["select"]
