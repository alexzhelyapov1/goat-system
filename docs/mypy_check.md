# How to Run MyPy Type Checks

MyPy is configured to perform static type checking on your Python codebase to help catch type-related errors early.

## Configuration

MyPy is configured using the `mypy.ini` file located in the project's root directory. This configuration currently specifies:
-   `files = app/`: Only files within the `app/` directory will be checked.
-   `ignore_missing_imports = True`: MyPy will ignore imports for which it cannot find type information. This is useful for third-party libraries that do not ship with their own type stubs.

## Running the Check

To run MyPy, navigate to the project's root directory in your terminal and execute the following command:

```bash
mypy app
```

This command will scan all Python files within the `app/` directory based on the `mypy.ini` configuration.

## Interpreting the Output

MyPy will output any type errors or warnings it finds. Each line typically follows this format:

```
<file_path>:<line_number>: <error_level>: <error_message>  [<error_code>]
```

For example:
-   `app/models.py:25: error: Name "db.Model" is not defined  [name-defined]` indicates an error on line 25 of `app/models.py`.
-   `app/telegram_utils.py:8: error: Incompatible default for argument "app_instance" (...)` indicates an error on line 8 of `app/telegram_utils.py`.

The `[error_code]` in brackets (e.g., `[name-defined]`, `[assignment]`) provides a specific identifier for the type of error, which can be useful for looking up more information or configuring MyPy to ignore specific error types.

## Next Steps

After running the check, you can address the reported errors to improve the type safety and reliability of your code.
