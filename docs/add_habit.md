# How to Add a New Habit

This document outlines how to add a new habit to your LifeOS system. Habits are a great way to track recurring activities and build consistent routines.

## Accessing the Habit Creation Form

1.  Log in to your LifeOS application.
2.  Navigate to the "Habits" section.
3.  Click on the "Create Habit" button.

## Habit Form Fields

The habit creation form includes the following fields:

*   **Name (Required)**: A short, descriptive name for your habit (e.g., "Drink Water", "Read Book", "Go to Gym").
*   **Description (Optional)**: A more detailed explanation of your habit, its purpose, or any specific notes you want to remember (e.g., "Drink 8 glasses of water daily", "Read for 30 minutes before bed").
*   **Start Date (Optional)**: The date from which you want to start tracking this habit. If left empty, it will default to the current date.
*   **End Date (Optional)**: The date until which you want to track this habit. If left empty, the habit will be tracked indefinitely.
*   **Strategy Type (Required)**: This defines how your habit is tracked and measured. Examples might include:
    *   `daily`: A habit you aim to complete every day.
    *   `weekly`: A habit you aim to complete a certain number of times per week.
    *   `monthly`: A habit you aim to complete a certain number of times per month.
    *   *(Note: The actual available strategy types depend on the application's backend implementation.)*
*   **Strategy Parameters (Optional)**: A JSON string containing additional parameters specific to the chosen `Strategy Type`.

    *   **Example for `weekly` strategy type**: To track a habit that you want to complete on specific days of the week (e.g., Monday, Wednesday, Friday), you can use the `days` parameter. The days are represented by numbers, where Monday is 0 and Sunday is 6.
        ```json
        {"days": [0, 2, 4]}
        ```
    *   **Example for `daily` strategy type**: To track a habit that you want to complete multiple times a day (e.g., 3 times), you can use the `frequency` parameter.
        ```json
        {"frequency": 3}
        ```

## Examples

Here are a few examples of how you might fill out the form:

### Example 1: Daily Water Intake (3 times a day)

*   **Name**: Drink Water
*   **Description**: Drink 8 glasses of water every day.
*   **Start Date**: (Leave empty, defaults to today)
*   **End Date**: (Leave empty, track indefinitely)
*   **Strategy Type**: `daily`
*   **Strategy Parameters**: `{"frequency": 3}`

### Example 2: Weekly Gym Visits (Mon, Wed, Fri)

*   **Name**: Go to Gym
*   **Description**: Visit the gym on Mondays, Wednesdays, and Fridays.
*   **Start Date**: `2026-01-01`
*   **End Date**: `2026-12-31`
*   **Strategy Type**: `weekly`
*   **Strategy Parameters**: `{"days": [0, 2, 4]}`

### Example 3: Read a Book Daily

*   **Name**: Read Book
*   **Description**: Read for 30 minutes every evening.
*   **Start Date**: (Leave empty)
*   **End Date**: (Leave empty)
*   **Strategy Type**: `daily`
*   **Strategy Parameters**: `{}` (or leave empty)

## Saving Your Habit

After filling in the required fields and any relevant optional fields, click the "Submit" button to save your new habit. You will then be redirected to the Habits list, where you can start tracking your progress.
