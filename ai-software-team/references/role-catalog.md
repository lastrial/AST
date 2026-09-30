# Role Catalog

Roles are temporary capabilities. `engineering_manager` belongs only to the root; a child has one primary role and at most one compatible secondary role.

| Role ID | Allowed duties |
| --- | --- |
| `engineering_manager` | planning, integration (root only) |
| `product_manager` | requirements |
| `requirements_analyst` | requirements |
| `project_planner` | planning, integration |
| `repository_analyst` | discovery |
| `solution_architect` | design, integration |
| `backend_architect` | design |
| `frontend_architect` | design |
| `api_architect` | design |
| `database_architect` | design |
| `distributed_systems_architect` | design |
| `cloud_architect` | design |
| `backend_developer` | implementation |
| `frontend_developer` | design, implementation |
| `mobile_developer` | design, implementation |
| `devops_engineer` | design, implementation, operations |
| `site_reliability_engineer` | design, review, operations |
| `release_engineer` | planning, implementation, operations, integration |
| `data_engineer` | design, implementation, test, operations |
| `ml_engineer` | design, implementation, test |
| `migration_engineer` | design, implementation, test, operations |
| `qa_engineer` | test |
| `test_automation_engineer` | test |
| `code_reviewer` | review |
| `security_reviewer` | review |
| `performance_reviewer` | review |
| `accessibility_reviewer` | review |
| `rag_architect` | design |
| `llm_engineer` | design, implementation, test |
| `vector_database_engineer` | design, implementation, test, operations |
| `storage_engineer` | design, implementation, test, operations |
| `workflow_engineer` | design, implementation, test |
| `observability_engineer` | design, implementation, test, review, operations |
| `developer_experience_engineer` | design, implementation, test |
| `devils_advocate` | challenge |

Builders never perform final review. In Assurance, challenge, build, test, and final review remain distinct. Challenge and review are always read-only.
