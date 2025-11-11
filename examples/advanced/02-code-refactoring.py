"""Advanced Example 2: Comprehensive Code Refactoring.

Demonstrates:
- Refactoring legacy code to modern TypeScript
- Adding type safety to untyped code
- Preserving behavior while improving structure
- Using validation to ensure correctness

Usage:
    python examples/advanced/02-code-refactoring.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Refactor legacy JavaScript to modern TypeScript."""
    print("Advanced Example 2: Code Refactoring")
    print("=" * 60)

    # Legacy JavaScript code
    legacy_code = """
// Legacy user management code
var users = [];

function addUser(name, email, role) {
    var user = {
        id: Math.random().toString(36),
        name: name,
        email: email,
        role: role || 'user',
        createdAt: new Date()
    };
    users.push(user);
    return user;
}

function findUser(id) {
    for (var i = 0; i < users.length; i++) {
        if (users[i].id === id) {
            return users[i];
        }
    }
    return null;
}

function updateUserRole(id, newRole) {
    var user = findUser(id);
    if (user) {
        user.role = newRole;
        return true;
    }
    return false;
}
"""

    print("Legacy Code (JavaScript):")
    print("-" * 60)
    print(legacy_code)
    print("-" * 60)

    config = Config()
    config.project.language = "typescript"
    config.constraints.type_enabled = True
    config.constraints.contextual_enabled = True

    pipeline = Pipeline(config)

    prompt = f"""Refactor this legacy JavaScript to modern TypeScript:

{legacy_code}

Requirements:
- Convert to TypeScript with full type annotations
- Use proper TypeScript classes or modern patterns
- Replace var with const/let
- Add interface for User type
- Use Array methods instead of for loops
- Add error handling
- Maintain all functionality"""

    print("\nRefactoring to TypeScript...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nRefactored Code (TypeScript):")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    if result.validation:
        print(f"\nValidation:")
        print(f"  Type Check: {'✅' if result.validation.type_valid else '❌'}")
        print(f"  Errors: {result.validation.errors_found}")

    pipeline.close()


if __name__ == "__main__":
    main()
