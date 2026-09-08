# Curated method provenance

Source: https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015

Inspected 2026-09-06, MIT license in LICENSE.md. Thirteen selected methods, bundled as
on-demand references beneath Guardian's existing skill. No whole-pack installer,
external discovery, executable scripts, background loops or extra runtime dependency.
These are adaptations, not unmodified upstream skills.

Intentional changes: native Codex file reads replace Claude-specific Skill calls;
existing user authorization and repository facts resolve routine choices; local planning
replaces automatic issue publication; native exact-tree handoff replaces automatic commits;
one final standards/spec arbiter replaces the two-subagent review cascade; optional
interface comparison replaces mandatory three-agent design. TDD retains red-first,
public behavior, independent oracles and vertical slices; independent acceptance is
owned separately. Team vocabulary wins over a generic glossary. Setup is once per
repository. Ancillary scripts, UI manifests and unrelated tracker templates are omitted.

## Source and distributed SHA-256

| Source file | Original SHA-256 | Distributed file | Adapted SHA-256 |
|---|---|---|---|
| skills/engineering/implement/SKILL.md | 6d3fd9e83b8f36e5213854779db49b256a457a7ebb4a503e53fa7dcff696adc3 | implement/METHOD.md | 5e0b9a3bf6d77946ddd957d0088e236254a476f30d7628858817d3e6822808ff |
| skills/engineering/tdd/mocking.md | 3ceb807fdf4a47d6a93d4d9a891e5ba6d362a6247bd08adc451feebfc17361ef | tdd/mocking.md | efedeae3e33ac4647fa2f8cffc4f910ee19d1aaefa9f4568173a1f72d66e60d7 |
| skills/engineering/tdd/tests.md | 859f9e592c188fda4fc7277dd180e4ce9c7a2e13f6efe1f6f29eccc9d28c106a | tdd/tests.md | 1b8fd1a4c72bad48a935abcdea162d5bed531cd47d0f35321cc8bb63a92ecf64 |
| skills/engineering/tdd/SKILL.md | cb01f66bebfaa25fa1f88e6b7e769cd9fd9f35b1120b8563749820738814c927 | tdd/METHOD.md | 4a4696fb169a84fcfb49a72cb3eae5daca67a749a7021bdca27f2a9927b435db |
| skills/engineering/code-review/SKILL.md | 47f4e52c21694def9c7c11cbfbf891ca35eac7a93e395797515be3c8a409ae50 | code-review/METHOD.md | 23fc4f5abb2325b53577f09cbd5f669b2be18b9ca3df7b99889b9c3673d5cafb |
| skills/engineering/codebase-design/DESIGN-IT-TWICE.md | 8e740bf98446dbd4dfdc132ac4346d9a7eedaf93de6a495889171cf7f99f16bd | codebase-design/DESIGN-IT-TWICE.md | 19aae4d52e8c5de5114081b0324c7fae4d57a8bc93b8ee480435192d3c8a1833 |
| skills/engineering/codebase-design/SKILL.md | 2c20617f87ec8af6a434859f381b2f061a69b530444e74eb39e78bb016a6d1e2 | codebase-design/METHOD.md | 26c80e20e01f386081f43dd6de9fb5c4105f91c315228aaf1cbac4330448f569 |
| skills/engineering/codebase-design/DEEPENING.md | f3dd099ce99289bd213914d8ee3e2429b78309c3957ca4583f7659551b1d53c1 | codebase-design/DEEPENING.md | 0d541f2cf2e55309fcd4af978496e3af490b87255c0e59defcd30b8a401a5939 |
| skills/engineering/diagnosing-bugs/SKILL.md | 77f3cf31bc99b2f49af943222526531fcc9fc41d047626d3640e875e85af3e84 | diagnosing-bugs/METHOD.md | 2c1c8e7e4c42d3df3e8852348badea38305fd3cd9d1b32d2c27c4289e0ce094a |
| skills/engineering/to-spec/SKILL.md | 43ad9cf318e5e7d3d1fa360253a37021796dc87a0c2e595ad262661a10f85088 | to-spec/METHOD.md | 0614414fd0399e94feea0f3507f7a0e41d8796ca08424160c5e4a97382c7e418 |
| skills/engineering/to-tickets/SKILL.md | 5c9fba69845c2519b9b35b9af42ae5142c21f8ca15ac2123dc2722002c8058ae | to-tickets/METHOD.md | 985f69c20de257d458b779fc1eb444dd0dcc8a24a56b8825fabf52c512923a09 |
| skills/productivity/grilling/SKILL.md | 10ff989e7498b23b5acb49d5048f11dcd906757d2f79c5cdf8a00001381296f2 | grilling/METHOD.md | 7f4f324754bfbab195fe5e92dc6ca9fca2af4b4d3926f72c548eb0b988262975 |
| skills/engineering/grill-with-docs/SKILL.md | 7de372c13488f1ee96cc11cd8907b56b6809cc93eef776eeddd37de6b6cbe3fe | grill-with-docs/METHOD.md | 7f93e73cef10cfa1bd2c42a14ba904a1ac1b45a0834250029aa3706f1de89485 |
| skills/engineering/domain-modeling/SKILL.md | 327a2b50620e2fd70abc6893cd6965e76b20f8d0adb0dc2c8d5eb3845efb643e | domain-modeling/METHOD.md | 027347113a988c26b3c49ecbefea431f43c9322862dfc82edb4f1fd88880a7b2 |
| skills/engineering/domain-modeling/CONTEXT-FORMAT.md | 17ab16ce783e4d2801ee52fd9acdf550cbf44de65ae76797a93943bbedf22a13 | domain-modeling/CONTEXT-FORMAT.md | 34497d4c0decc930f35e6e234c7d4c1362e91d60609937479ea09c3d60853dca |
| skills/engineering/domain-modeling/ADR-FORMAT.md | 944c92aa790e8fbdc9199640b170979abb8a34ba8d0fe18c2a01a63bce140ca0 | domain-modeling/ADR-FORMAT.md | 498892240c9939db6bc610af1e6be34f47e74c2523b8d43d0caad74a9752d12c |
| skills/productivity/writing-for-agents/SKILL.md | 551adca942227b44192edba88acd4e8db911f0121ce58ad16944ccf6a896a74a | writing-for-agents/METHOD.md | b548555ecbf90044241fe8e83ac959b812315e85f78084c25f1c625476f19db4 |
| skills/productivity/handoff/SKILL.md | 7c62de979fdc7ac32fb5ddb2146156c917f80ee070d30fadc9d40343c4b6ed25 | handoff/METHOD.md | 56376473da68ed5ea18cd9cb74964a50b25af198521ad374f3c91c569a0e821f |
| skills/engineering/setup-matt-pocock-skills/SKILL.md | 2bcd89e97777cdb705914424e39c97d5db524c8eb4eafac8120778a07774f0ec | setup-matt-pocock-skills/METHOD.md | 6a75f5249f7ca7a21b38afaa2ca73819e1c4c701100abd25189e5b10af316c20 |

The distributed methods use native snapshots, local planning and discovery of the
target environment. The hashes identify the upstream source and packaged adaptations.
