def format_serializer_error(errors: dict) -> str:
    if not errors:
        return "Ocorreu um erro de validação."
    
    # Retorno dos errors do serializer =>
    # {
    #     'field': [
    #        'campo é required'
    #      ]
    # }
    for field, messages in errors.items():
        if field == 'non_field_errors':
            field = 'erro'

        if messages and isinstance(messages, list):
            return f"{field}: {messages[0]}" # o retorno ficará assim => title: campo é required
        elif isinstance(messages, dict):
            nested = format_serializer_error(messages)
            return f"{field}: {nested}"
        
    return "Ocorreu um erro de validação."