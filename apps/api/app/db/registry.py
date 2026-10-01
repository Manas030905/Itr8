"""Import every model module so SQLAlchemy/Alembic see the full metadata.

Add new modules' models here as they are created.
"""

from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.profiles import models as _profiles_models  # noqa: F401
from app.modules.skills import models as _skills_models  # noqa: F401
from app.modules.users import models as _users_models  # noqa: F401
