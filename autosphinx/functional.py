KEY = "# ADD_DOC"
# __KEY__ = ""
CLASS_DEF = "class "
FUNCTION_DEF = "def "
METHOD_DEF = f"    {FUNCTION_DEF}"

CLASS_DEF_PRIVATE = f"{CLASS_DEF}_"
FUNCTION_DEF_PRIVATE = f"{FUNCTION_DEF}_"
METHOD_DEF_PRIVATE = METHOD_DEF.replace(FUNCTION_DEF, FUNCTION_DEF_PRIVATE)

def starts_with(line, pattern):
    return line[:len(pattern)] == pattern
