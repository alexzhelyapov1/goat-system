# Frontend Setup Instructions

This document outlines the steps to set up the React frontend application using Vite, TypeScript, and Tailwind CSS.

## Step 1: Create Vite React + TypeScript Project

npm install -g npm@latest
We will use `npm create vite@latest` to scaffold the new React project.

**Command to execute:**

```bash
npm create vite@latest frontend -- --template react-ts
```
# ? sudo sysctl fs.inotify.max_user_watches=524288

**What to expect and choose:**

1.  You might be asked to install `create-vite`. Type `y` and press Enter.
    ```
    Need to install the following packages:
      create-vite@latest
    Ok to proceed? (y)
    ```
2.  The command will then proceed to create the project in the `frontend/` directory. You will not be prompted for further input during this specific command execution beyond the initial installation confirmation.

## Step 2: Install Dependencies and Configure Tailwind CSS

Navigate into the newly created `frontend` directory and install the required packages.

**Commands to execute:**

```bash
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer axios
npx tailwindcss init -p

rm -rf node_modules package-lock.json
npm install
npx tailwindcss init -p
```

**What to expect and choose:**

1.  `cd frontend`: This will change your current directory to `frontend`.
2.  `npm install`: This will install the default dependencies for the Vite project.
3.  `npm install -D tailwindcss postcss autoprefixer axios`: This will install Tailwind CSS, PostCSS, Autoprefixer as development dependencies, and Axios as a regular dependency.
4.  `npx tailwindcss init -p`: This command will initialize Tailwind CSS.
    *   It will create `tailwind.config.js` and `postcss.config.js` in the `frontend` directory. No interactive choices are required for this command.

## Step 3: Configure Tailwind CSS in `tailwind.config.js` and `index.css`

After the above steps, you'll need to modify the generated `tailwind.config.js` and the main CSS file to include Tailwind's directives.

**Action:** Update `frontend/tailwind.config.js`
Replace the content of `frontend/tailwind.config.js` with the following:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Action:** Update `frontend/src/index.css`
Add the Tailwind directives to `frontend/src/index.css`. You might need to create this file if it doesn't exist, or modify `frontend/src/main.tsx` to import it (Vite templates often use `index.css` by default).

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Action:** Remove existing `App.css` and `index.css` (or `main.css`) content
The Vite default template includes some CSS in `src/App.css` and `src/index.css`. For a clean Tailwind setup, it's best to remove the default styling.

*   Delete the content of `frontend/src/App.css`.
*   If `frontend/src/index.css` (or `main.css`) has default content, clear it before adding the Tailwind directives.

Once these manual steps are done, the frontend project will be set up with React, TypeScript, and Tailwind CSS.
