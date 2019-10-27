
from glom.core import (glom,
                       Fill,
                       Auto,
                       register,
                       Glommer,
                       Call,
                       Invoke,
                       Spec,
                       OMIT,  # backwards compat
                       SKIP,
                       STOP,
                       UP,
                       ROOT,
                       MODE,
                       Check,
                       Path,
                       Literal,
                       Coalesce,
                       Inspect,
                       GlomError,
                       CheckError,
                       PathAccessError,
                       CoalesceError,
                       UnregisteredTarget,
                       T, S)

from glom.reduction import Sum, Fold, Flatten, flatten, FoldError, Merge, merge
from glom.mutation import Assign, assign, PathAssignError

# there's no -ion word that really fits what "streaming" means.
# generation, production, iteration, all have more relevant meanings
# elsewhere. (maybe procrastination :P)
from glom.streaming import Iter
