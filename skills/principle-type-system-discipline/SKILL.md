---
name: principle-type-system-discipline
description: "Apply when designing types, reviewing a function signature, or writing code in any statically-typed language. Make illegal states unrepresentable, brand semantic primitives, parse external data at boundaries, exhaust variants, derive from authoritative schemas."
disable-model-invocation: true
---

# Type System Discipline

Make the compiler reject impossible states, mismatched primitives, and unhandled variants. Prefer defining errors and special cases out of existence over proliferating handlers. For TypeScript syntax, see the `typescript-best-practices` skill.

- **Make bad states impossible to write.** Use sum types (tagged unions, enums with data), not a bag of optional fields. `{ done: boolean; doneAt?: Date }` allows `done: true` with no date. Use `{ kind: 'open' } | { kind: 'done'; at: Date }`. If you need a comment to say which field combinations are valid, split it into a sum type.
- **Build types from the values you want.** Do not cut a loose type down with checks. A non-empty list is a head plus a rest.
- **Brand semantic primitives.** `UserId` and `OrderId` are strings underneath but should not be interchangeable. Give each its own type, such as a branded intersection in TypeScript or a newtype elsewhere. Validate once at creation, trust the type downstream. If two arguments share a primitive type but mean different things, brand them.
- **External data is untyped until parsed.** RPC payloads, JSON, IPC messages, CLI args, config files, environment variables, database rows. Have a parse function at every boundary that turns unstructured input into the typed model. The **boundary-discipline** principle skill says where to put validation.
- **Do not lie to the compiler.** Each cast (`as`, `any`, a non-null assertion) is a crash waiting to happen. Prove the fact, or move the check to the boundary.
- **Make matches exhaustive,** so a new case breaks the build where it is not handled (`never` in TypeScript, `match` in Rust).
- **Derive types from authoritative schemas.** When a protocol buffer, OpenAPI spec, GraphQL schema, database migration, design-token file, or another file owns a shape, derive from it instead of hand-rolling a parallel type. See the **encode-lessons-in-structure** principle skill.
- **Make a type stronger only where code would otherwise fail.** A "should never happen" throw shows where a type is too weak. Fix that one, then stop.
