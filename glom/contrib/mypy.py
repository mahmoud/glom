from typing import Type

from mypy.plugin import Plugin, FunctionContext
from mypy.types import Type as MypyType


class _GlomPlugin(Plugin):
    def get_function_hook(self, fullname: str) -> MypyType:
        if fullname == 'glom.core.glom':
            def test(ctx: FunctionContext) -> MypyType:
                print(ctx)
                print(ctx.arg_types[0][0], ctx.arg_types[1][0])
                print(ctx.arg_types[1][0].last_known_value.value)
                return ctx.api.expr_checker.analyze_external_member_access(
                    ctx.arg_types[1][0].last_known_value.value,
                    ctx.arg_types[0][0],
                    ctx.context,
                )
            return test
        return None


def plugin(version: str) -> Type[Plugin]:
    return _GlomPlugin
