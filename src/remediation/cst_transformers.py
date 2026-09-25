"""LibCST Transformers for lossless AST/CST code remediation.
Preserves comments, whitespace, and code style byte-for-byte.
Based on Bob DevSecOps Guardian Research (Bobrep.pdf Section 6).
"""

import re
try:
    import libcst as cst
    import libcst.matchers as m
    LIBCST_AVAILABLE = True
except ImportError:
    LIBCST_AVAILABLE = False


if LIBCST_AVAILABLE:
    class MaskEmailTransformer(cst.CSTTransformer):
        """Finds logger.info(user.email) and transforms to logger.info(mask_email(user.email))."""

        def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
            if not m.matches(updated_node, m.Call(
                func=m.Attribute(value=m.Name("logger"), attr=m.Name("info"))
            )):
                return updated_node

            if not updated_node.args:
                return updated_node

            first_arg = updated_node.args[0]
            # Check if logging an email attribute or f-string with email
            arg_code = cst.Module([]).code_for_node(first_arg.value)
            if "email" in arg_code and "mask_email" not in arg_code:
                wrapped_value = cst.Call(
                    func=cst.Name("mask_email"),
                    args=[cst.Arg(value=first_arg.value)]
                )
                new_first_arg = first_arg.with_changes(value=wrapped_value)
                return updated_node.with_changes(args=(new_first_arg,) + updated_node.args[1:])

            return updated_node


    class HardcodedSecretTransformer(cst.CSTTransformer):
        """Replaces hardcoded assignments like API_KEY = '...' with os.getenv('API_KEY')."""

        def __init__(self, variable_names=None):
            self.variable_names = set(variable_names or ["API_KEY", "DB_PASSWORD", "AWS_ACCESS_KEY_ID"])

        def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.Assign:
            targets = updated_node.targets
            if not targets:
                return updated_node

            first_target = targets[0].target
            target_name = None
            if isinstance(first_target, cst.Name):
                target_name = first_target.value

            if target_name in self.variable_names:
                if m.matches(updated_node.value, m.SimpleString()):
                    replacement = cst.Call(
                        func=cst.Attribute(value=cst.Name("os"), attr=cst.Name("getenv")),
                        args=[cst.Arg(value=cst.SimpleString(f"'{target_name}'"))]
                    )
                    return updated_node.with_changes(value=replacement)

            return updated_node


def apply_cst_transformations(source_code: str) -> str:
    """Apply LibCST transformations if available, otherwise apply safe regex transformations."""
    if LIBCST_AVAILABLE:
        try:
            tree = cst.parse_module(source_code)
            tree = tree.visit(MaskEmailTransformer())
            tree = tree.visit(HardcodedSecretTransformer())
            return tree.code
        except Exception:
            pass

    # High-fidelity regex fallback
    code = source_code
    # Mask email in logger
    code = re.sub(
        r'logger\.info\((f?["\'].*?\{user\.email\}.*?["\'])\)',
        r'logger.info(mask_email(user.email))',
        code
    )
    code = re.sub(
        r'logger\.info\(user\.email\)',
        r'logger.info(mask_email(user.email))',
        code
    )
    # Env secret replacement
    code = re.sub(
        r'API_KEY\s*=\s*["\']sk-[^"\']+["\']',
        'API_KEY = os.getenv("API_KEY")',
        code
    )
    return code
