import js from '@eslint/js'
import simpleImportSort from 'eslint-plugin-simple-import-sort'
import unusedImports from 'eslint-plugin-unused-imports'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  {
    ignores: [
      'dist/**',
      '.output/**',
      '.nitro/**',
      '.vinxi/**',
      'node_modules/**',
      'src/routeTree.gen.ts',
      'src/api/generated/schema.ts',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.node },
    },
    plugins: {
      'simple-import-sort': simpleImportSort,
      'unused-imports': unusedImports,
    },
    rules: {
      // We rely on simple-import-sort + unused-imports for the autofixers.
      // Disable the base rules that conflict.
      '@typescript-eslint/no-unused-vars': 'off',
      'no-unused-vars': 'off',

      'unused-imports/no-unused-imports': 'error',
      'unused-imports/no-unused-vars': [
        'warn',
        {
          vars: 'all',
          varsIgnorePattern: '^_',
          args: 'after-used',
          argsIgnorePattern: '^_',
          caughtErrors: 'all',
          caughtErrorsIgnorePattern: '^_',
        },
      ],

      // Custom groups: side-effect → react/node → external → @/ → relative → styles
      'simple-import-sort/imports': [
        'error',
        {
          groups: [
            ['^\\u0000'], // side-effect imports
            ['^node:', '^react$', '^react-dom', '^react/'],
            ['^@?\\w'], // other external packages
            ['^@/'], // internal alias
            ['^\\.\\.(?!/?$)', '^\\.\\./?$', '^\\./(?=.*/)(?!/?$)', '^\\.(?!/?$)', '^\\./?$'],
            ['^.+\\.s?css$'], // styles last
          ],
        },
      ],
      'simple-import-sort/exports': 'error',

      // Prefer `import type` for type-only specifiers.
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { prefer: 'type-imports', fixStyle: 'separate-type-imports' },
      ],
    },
  },
  {
    files: ['src/components/**/*.{ts,tsx}', 'src/routes/**/*.{ts,tsx}'],
    ignores: [
      'src/components/ui/**',
      'src/routes/tags/$tagId.tsx',
      'src/routes/tags/new.tsx',
    ],
    rules: {
      'no-restricted-syntax': [
        'error',
        {
          selector: "Literal[value=/#[0-9a-fA-F]{3,6}\\b/]",
          message:
            'No raw hex literals in components/routes — use a CSS-var-backed Tailwind class (defined in src/theme/). See docs/CODING_GUIDELINES.md §1.8.',
        },
        {
          selector: "TemplateElement[value.raw=/#[0-9a-fA-F]{3,6}\\b/]",
          message:
            'No raw hex literals in components/routes — use a CSS var (defined in src/theme/). See docs/CODING_GUIDELINES.md §1.8.',
        },
        // C22: Shadcn-only UI primitives. Use Input, Select, Textarea, Button,
        // Table, Dialog, Collapsible, Progress, Checkbox, RadioGroup from
        // @/components/ui/ instead of native HTML primitives.
        // <form> is exempt: shadcn Form is FormProvider (RHF), not a <form> renderer.
        {
          selector:
            "JSXOpeningElement[name.type='JSXIdentifier'][name.name=/^(input|select|textarea|button|table|dialog|details|progress)$/]",
          message:
            'No native HTML primitive in components/routes — use the shadcn equivalent from @/components/ui/. See docs/IMPLEMENTATION_PLAN.md (C22).',
        },
      ],
    },
  },
  {
    // Loosen rules in tests
    files: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
)
