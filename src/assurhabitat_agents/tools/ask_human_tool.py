def ask_human(message: str) -> str:
    """Ask for user input.

    Parameters
    ----------
    message : str
        The message to indicates to the user what data is needed. (required)

    Returns:
    -------
    str
        The user's input.
    """
    return input(message)