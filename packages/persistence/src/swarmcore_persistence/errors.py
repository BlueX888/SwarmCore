class PersistenceConflictError(RuntimeError):
    pass


class IdempotencyConflictError(PersistenceConflictError):
    pass


class TransitionConflictError(PersistenceConflictError):
    pass
