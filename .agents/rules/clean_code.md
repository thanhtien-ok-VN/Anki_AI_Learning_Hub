# Rules: Clean Code, SOLID Principles, Cleanup & Reliability Guidelines

## 1. SOLID Principles (5 Nguyên tắc Thiết kế Phần mềm)
- **S - Single Responsibility Principle (SRP):** Single responsibility per class/module/function. Each component has one reason to change.
- **O - Open/Closed Principle (OCP):** Software entities should be open for extension, but closed for modification. Extend behavior via polymorphism or composition instead of mutating stable core logic.
- **L - Liskov Substitution Principle (LSP):** Derived classes must be completely substitutable for their base classes without breaking program correctness.
- **I - Interface Segregation Principle (ISP):** Prefer small, specific interfaces/mixins over large, monolithic ones. Clients should not be forced to depend on methods they do not use.
- **D - Dependency Inversion Principle (DIP):** High-level modules should not depend on low-level modules; both should depend on abstractions (abstract base classes/interfaces).

## 2. Cleanup & Dead Code (Dọn dẹp & Xóa mã nguồn)
- **No Commented Code:** Delete unused or old code completely. Never leave commented-out code (`//`, `#`, `/* */`).
- **No Revision History in Code:** Do not add meta comments like `// Updated by AI` or `// Fixed bug X`. Git tracks history.
- **Minimal Documentation:** Only comment non-obvious algorithms or complex business logic ("why"), never explain plain code ("what").

## 3. Clean Code & Style (Code gọn & Chuẩn hóa)
- **KISS (Keep It Simple, Stupid):** Prefer the simplest working solution. Avoid over-engineering or extra abstraction layers unless requested.
- **Single Responsibility:** Functions should focus on a single task. Consider splitting functions if they exceed 20-30 lines.
- **Self-Documenting Names:** Use clear English for variables, functions, and classes. Avoid confusing abbreviations (`a`, `temp`, `data1`).
- **Modern Syntax:** Leverage modern syntax features (destructuring, optional chaining, list comprehensions, async/await).

## 4. Correctness & Reliability (Tính đúng đắn & Tin cậy)
- **Strict Error Handling & Type Safety:** Use Type Hints / TypeScript types and handle edge cases immediately where errors might occur.
- **Preserve Context & Architecture:** Adhere strictly to existing project conventions, libraries, and architecture.
- **No Halting / Placeholders:** Provide complete, production-ready implementation without skipping blocks or using placeholders (`// ... rest of code`).
