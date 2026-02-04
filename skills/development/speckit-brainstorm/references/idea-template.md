# idea.md Template

Use this template when creating the idea.md file for a new feature.

---

# Feature: [Feature Name]

## Summary

[1-2 sentence description of what this feature does]

## Problem Statement

[What problem does this feature solve? Why is it needed?]

## User Stories

- As a [user type], I want to [action] so that [benefit]
- As a [user type], I want to [action] so that [benefit]

## Requirements

### Must Have (P0)

Core functionality that MUST be implemented:

- [ ] [Requirement 1]
- [ ] [Requirement 2]
- [ ] [Requirement 3]

### Nice to Have (P1)

Features to include if time permits:

- [ ] [Optional feature 1]
- [ ] [Optional feature 2]

### Out of Scope

Explicitly excluded from this feature:

- [Item 1] - [Reason]
- [Item 2] - [Reason]

## Technical Approach

### Architecture

[High-level architecture decisions]

### Database Changes

[Any new tables, columns, or migrations needed]

- Table: `table_name`
  - `column_name` (type): description

### API Changes

[New or modified endpoints]

- `POST /api/v2/endpoint` - Description
- `GET /api/v2/endpoint/:id` - Description

### UI/UX

[User interface considerations]

- Page: [page name]
- Components: [component list]

## Affected Components

### Backend

- `packages/backend/src/path/to/file.rs`
- `packages/backend/src/path/to/other.rs`

### Frontend

- `packages/node-ui/src/pages/PageName.tsx`
- `packages/node-ui/src/components/ComponentName.tsx`

## Dependencies

[External dependencies or prerequisites]

- Requires: [dependency]
- Depends on: [other feature/ticket]

## Testing Strategy

[How will this feature be tested?]

- Unit tests for: [components]
- Integration tests for: [flows]
- Manual testing: [scenarios]

## Open Questions

[Any unresolved questions to address during clarify phase]

1. [Question 1]
2. [Question 2]

## Success Criteria

[How do we know this feature is complete?]

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

---

## Notes

[Any additional notes, references, or context]
