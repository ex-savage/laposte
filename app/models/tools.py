from sqlalchemy import sql
from sqlalchemy.dialects.sqlite.base import (
    SQLiteCompiler,
    SQLiteDialect,
    SQLiteIdentifierPreparer,
)

reserved_words = SQLiteIdentifierPreparer.reserved_words
reserved_words.add("returning")


class CustomSQLiteIdentifierPreparer(SQLiteIdentifierPreparer):
    reserved_words = reserved_words


def returning_clause(self, stmt, returning_cols):
    """Adds compile logic for RETURNING clause."""
    columns = [self._label_returning_column(stmt, c) for c in sql.expression._select_iterables(returning_cols)]
    return "RETURNING " + ", ".join(columns)


SQLiteDialect.preparer = CustomSQLiteIdentifierPreparer
SQLiteDialect.implicit_returning = True
SQLiteDialect.preparer.full_returning = True
SQLiteCompiler.returning_clause = returning_clause

from sqlalchemy.dialects.sqlite import insert  # noqa
