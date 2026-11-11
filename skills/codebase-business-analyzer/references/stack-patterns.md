# Stack patterns — where each concept lives

Read only the sections matching the detected stack. "Roles" = role/permission definitions and checks; "Validation" = server-side required fields and rules.

## Contents
- Backend: Laravel · Node/Express · NestJS · Django/DRF · FastAPI/Flask · Spring Boot · ASP.NET Core · Rails · Go
- Frontend: React/Next.js · Vue/Nuxt · Angular · Blazor · Mobile (Flutter / React Native)
- Database / ORM
- Auth providers

---

## Backend

### Laravel (PHP)
- Routes: `routes/web.php`, `routes/api.php`, `routes/*.php`; `php artisan route:list` output if user provides it.
- Controllers: `app/Http/Controllers/**`. Business logic often in `app/Services`, `app/Actions`, `app/Repositories`.
- Models: `app/Models/**` — `$fillable`, `$casts`, relations (`hasMany`, `belongsTo`, `belongsToMany`), scopes (`scopeXxx`, global scopes = data-scope rules), `boot()` hooks.
- Observers / events: `app/Observers`, `app/Events`, `app/Listeners`, `EventServiceProvider`.
- Validation: `app/Http/Requests/**` (`rules()`, `authorize()`), inline `$request->validate([...])`, `Validator::make`.
- Roles: `app/Policies/**`, `AuthServiceProvider` (`Gate::define`), middleware in `app/Http/Kernel.php` or `bootstrap/app.php`; Spatie permission (`role:`, `permission:` middleware, `hasRole`, `givePermissionTo`, seeders in `database/seeders`).
- DB: `database/migrations/**`, `database/seeders/**`.
- Jobs/schedule: `app/Jobs`, `app/Console/Kernel.php` or `routes/console.php`, `app/Notifications`, `app/Mail`.
- Filament/Nova admin: `app/Filament/Resources/**` — forms (`form()`), tables, `canViewAny()` etc.

### Node.js / Express
- Routes: `routes/**`, `src/routes/**`, files calling `router.get/post/...` or `app.use('/path', ...)`.
- Middleware for auth/roles: functions named `auth`, `authorize`, `requireRole`, `isAdmin`, `checkPermission`.
- Validation: Joi / Zod / Yup / express-validator (`body('x').notEmpty()`), celebrate.
- Models: Mongoose `Schema({ field: { required: true } })`, Sequelize `define`/`init`, Prisma, TypeORM, Drizzle (`pgTable(...)`, `.notNull()`, `pgEnum`, `relations()`; migrations in `drizzle/` or `migrations/*.sql`).

### NestJS
- Modules: `*.module.ts` (= module boundaries and dependencies via `imports`).
- Controllers: `*.controller.ts` (`@Get`, `@Post`...). Services: `*.service.ts`.
- DTOs: `*.dto.ts` with class-validator (`@IsNotEmpty`, `@IsOptional`, `@ValidateIf` = conditional).
- Roles: `@UseGuards(...)`, custom `@Roles()` decorators, `*.guard.ts`, CASL `ability.factory.ts`.
- Entities: `*.entity.ts` (TypeORM) or `schema.prisma`.
- Events/jobs: `@OnEvent`, `@Cron`, Bull processors (`@Processor`).

### Django / DRF (Python)
- URLs: `urls.py` per app. Apps (`INSTALLED_APPS`) ≈ modules.
- Views: `views.py`, `viewsets.py`. Serializers (validation): `serializers.py` (`required=`, `validate_<field>`, `validate`).
- Forms: `forms.py` (`required=`, `clean_<field>`).
- Models: `models.py` (`null=False, blank=False` = required; `choices` = enums; `Meta.constraints`).
- Roles: `permission_classes`, `permissions.py`, `@permission_required`, `Group`/`Permission` fixtures, `has_perm`, `get_queryset` filters (= data scope).
- Signals: `signals.py`; tasks: Celery `tasks.py`, `CELERY_BEAT_SCHEDULE`.
- Admin: `admin.py`.
- Migrations: `*/migrations/*.py`.

### FastAPI / Flask
- Routers: `APIRouter`, `@app.get`, Flask `Blueprint`, `@bp.route`.
- Validation: Pydantic models (`Field(...)` = required, `Optional[...] = None` = optional, validators), Marshmallow, WTForms.
- Roles: `Depends(get_current_user)`, custom dependencies like `require_role`, Flask-Login/Flask-Principal decorators.
- Models: SQLAlchemy (`nullable=False`), Alembic `versions/`.

### Spring Boot (Java/Kotlin)
- Controllers: `@RestController`, `@RequestMapping`, `@GetMapping`...
- Services: `@Service`; repositories: `@Repository`, Spring Data query methods (data scope in custom queries).
- Validation: DTOs with `@NotNull`, `@NotBlank`, `@Size`, `@Valid`; custom `ConstraintValidator`.
- Roles: `SecurityConfig` / `SecurityFilterChain` (`.requestMatchers(...).hasRole(...)`), `@PreAuthorize`, `@Secured`, `@RolesAllowed`.
- Entities: `@Entity`, `@Column(nullable=false)`, `@OneToMany`, `@Enumerated`.
- Migrations: `db/migration/V*.sql` (Flyway), `db/changelog` (Liquibase).
- Jobs/events: `@Scheduled`, `@EventListener`, `@KafkaListener`, `@RabbitListener`.

### ASP.NET Core (C#)
- Controllers: `Controllers/**` (`[HttpGet]`, `[Route]`), Minimal APIs (`app.MapGet`), Razor Pages `Pages/**`.
- Validation: DataAnnotations (`[Required]`, `[StringLength]`), FluentValidation `AbstractValidator<T>`.
- Roles: `[Authorize(Roles = "...")]`, `[Authorize(Policy = "...")]`, `AddAuthorization(o => o.AddPolicy(...))`, `IAuthorizationHandler`.
- Entities: `DbContext` (`DbSet<>`), `OnModelCreating` (`.IsRequired()`, `HasOne/WithMany`), `Migrations/**`.
- Background: `IHostedService`, Hangfire, MediatR handlers (`*Handler.cs` = business logic in CQRS).

### Ruby on Rails
- Routes: `config/routes.rb`. Controllers: `app/controllers`. Models: `app/models` (`validates :x, presence: true`, `belongs_to`, `has_many`, `enum`, callbacks).
- Roles: Pundit `app/policies`, CanCanCan `app/models/ability.rb`, `before_action`.
- DB: `db/schema.rb`, `db/migrate`. Jobs: `app/jobs`, Sidekiq.

### Go
- Routers: gin/echo/chi/fiber (`r.GET`, `e.POST`, `r.Route`), handlers packages.
- Validation: `validate:"required"` struct tags (go-playground/validator), `binding:"required"` (gin).
- Roles: middleware funcs, Casbin `model.conf` + `policy.csv`.
- Models: GORM structs (`gorm:"not null"`), sqlc queries, `migrations/*.sql`.

---

## Frontend

### React / Next.js
- Routes/pages: `app/**/page.tsx` (App Router), `pages/**` (Pages Router), React Router config (`createBrowserRouter`, `<Route path=...>`).
- Route guards: `middleware.ts` (Next), `ProtectedRoute`/`RequireAuth`/`RoleGuard` components, layout-level checks.
- Menus/navigation by role: `sidebar`, `menu`, `nav` config files with `roles`/`permissions` arrays.
- Forms: react-hook-form (`register('x', { required })`, `zodResolver(schema)`), Formik + Yup (`validationSchema`), Ant Design `Form.Item rules={[{ required: true }]}`, MUI fields with `required`.
- API calls: `services/`, `api/`, `lib/api`, RTK Query / React Query hooks — maps pages ↔ endpoints.
- Server actions (`'use server'`) are backend logic — treat them as backend.

### Vue / Nuxt
- Routes: `router/index.(js|ts)` (`meta: { roles }`), Nuxt `pages/**`, `middleware/**`.
- Guards: `router.beforeEach`, Nuxt route middleware.
- Forms: VeeValidate (`rules="required"`, `useForm` + yup/zod), Vuelidate (`required`), Element Plus/Vuetify `rules`.
- Role checks: `v-if="hasRole(...)"`, `v-can`, custom directives, Pinia/Vuex auth store.

### Angular
- Routes: `*-routing.module.ts`, `app.routes.ts` (`canActivate`, `data: { roles }`).
- Guards: `*.guard.ts`. Directives like `*hasPermission`.
- Forms: Reactive forms (`Validators.required`, `FormBuilder.group`), template-driven (`required` attribute).
- Services: `*.service.ts` (HTTP calls → endpoints).

### Blazor
- Pages: `@page` directives in `*.razor`; `[Authorize]`, `<AuthorizeView Roles="...">`.
- Forms: `<EditForm>` + DataAnnotations / FluentValidation on the model.

### Mobile (Flutter / React Native)
- Flutter: screens in `lib/**/screens|pages|views`, `TextFormField(validator:)`, routing (`GoRouter`, `routes:`), role checks in providers/blocs.
- React Native: same as React; navigation in `navigation/**`.

---

## Database / ORM quick map

| Concept | Where to look |
|---|---|
| Required column | `NOT NULL`, `nullable=False`, `->nullable()` absent, `@Column(nullable=false)`, `.IsRequired()`, Prisma field without `?` |
| Enum / status | DB `ENUM`, check constraints, `choices`, PHP/TS/Java enums, Prisma `enum` |
| Relations | FKs, `references`, ORM relation decorators, pivot/join tables |
| Hidden rules | triggers, stored procedures, views, check constraints, default values, `ON DELETE CASCADE` |
| Seed roles/permissions | seeders, fixtures, `data.sql`, initial migrations inserting rows |

Raw SQL dumps (`*.sql`), `schema.prisma`, `db/schema.rb`, `structure.sql`, EF model snapshots give a full schema in one file — prefer them over reading every migration.

## Auth providers (roles may live outside the code)
- Keycloak / Auth0 / Cognito / Azure AD / Firebase: roles defined in the provider; code only reads claims (`realm_access.roles`, `custom:role`, `groups`). Document claim names and note that role definitions are external.
- JWT: inspect token payload construction (where `role`/`permissions` are added at login).
- Permissions stored in DB and assigned at runtime: document the mechanism and the seeded defaults; note that production data may differ.
