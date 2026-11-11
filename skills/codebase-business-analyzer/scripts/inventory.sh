#!/usr/bin/env bash
# Read-only inventory of a codebase for business analysis.
# Usage: inventory.sh <project-root> [max-files-per-category]
# Prints detected stacks and candidate files per category. Never modifies anything.
set -u

ROOT="${1:-.}"
MAX="${2:-60}"
if [ ! -d "$ROOT" ]; then echo "Not a directory: $ROOT" >&2; exit 1; fi
cd "$ROOT" || exit 1

EXCLUDES=(--exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=.git --exclude-dir=dist
  --exclude-dir=build --exclude-dir=.next --exclude-dir=.nuxt --exclude-dir=out --exclude-dir=target
  --exclude-dir=bin --exclude-dir=obj --exclude-dir=coverage --exclude-dir=__pycache__ --exclude-dir=.venv
  --exclude-dir=venv --exclude-dir=.vercel --exclude-dir=.idea --exclude-dir=.output --exclude-dir=.turbo --exclude-dir=.cache --exclude-dir=storage --exclude-dir=public --exclude-dir=.dart_tool)
INCLUDES=(--include=*.php --include=*.js --include=*.jsx --include=*.ts --include=*.tsx --include=*.vue
  --include=*.py --include=*.java --include=*.kt --include=*.cs --include=*.razor --include=*.rb
  --include=*.go --include=*.dart --include=*.sql --include=*.prisma --include=*.svelte)

section() { printf '\n## %s\n' "$1"; }

# grep -E across code files; print matching paths with match counts, top N.
find_by_content() {
  grep -rlE "${INCLUDES[@]}" "${EXCLUDES[@]}" "$1" . 2>/dev/null \
    | grep -vE '\.(min|test|spec)\.|/tests?/|/__tests__/' | sort | head -n "$MAX"
}

# find by path pattern (extended regex on path)
find_by_path() {
  find . -type f \( -path '*/node_modules' -o -path '*/vendor' -o -path '*/.git' -o -path '*/dist' \
    -o -path '*/build' -o -path '*/.next' -o -path '*/target' -o -path '*/obj' -o -path '*/bin' \) -prune -o \
    -type f -print 2>/dev/null | grep -E "$1" | grep -vE '/(node_modules|vendor|\.git|dist|build|\.next|target|obj|bin)/' \
    | grep -vE '/\.[^/]+/|\.map$' | sort | head -n "$MAX"
}

echo "# Inventory: $(pwd)"

section "Manifests (stack detection)"
find_by_path '/(package\.json|composer\.json|requirements[^/]*\.txt|pyproject\.toml|Pipfile|pom\.xml|build\.gradle(\.kts)?|[^/]+\.csproj|go\.mod|Gemfile|pubspec\.yaml|docker-compose[^/]*\.ya?ml|\.env\.example)$'

section "Detected frameworks"
detect() { if grep -rqsE "$2" --include="$3" "${EXCLUDES[@]}" . 2>/dev/null; then echo "- $1"; fi; }
detect "Laravel"        '"laravel/framework"'       'composer.json'
detect "Spatie Permission" '"spatie/laravel-permission"' 'composer.json'
detect "Filament"       '"filament/filament"'       'composer.json'
detect "NestJS"         '"@nestjs/core"'            'package.json'
detect "Express"        '"express"'                 'package.json'
detect "Next.js"        '"next"'                    'package.json'
detect "React"          '"react"'                   'package.json'
detect "Vue"            '"vue"'                     'package.json'
detect "Nuxt"           '"nuxt"'                    'package.json'
detect "Angular"        '"@angular/core"'           'package.json'
detect "Svelte"         '"svelte"'                  'package.json'
detect "React Native"   '"react-native"'            'package.json'
detect "Prisma"         '"@prisma/client"|"prisma"' 'package.json'
detect "TypeORM"        '"typeorm"'                 'package.json'
detect "Sequelize"      '"sequelize"'               'package.json'
detect "Drizzle"        '"drizzle-orm"'             'package.json'
detect "Mongoose"       '"mongoose"'                'package.json'
detect "Zod"            '"zod"'                     'package.json'
detect "Yup"            '"yup"'                     'package.json'
detect "react-hook-form" '"react-hook-form"'        'package.json'
detect "Formik"         '"formik"'                  'package.json'
detect "CASL"           '"@casl/'                   'package.json'
detect "Django"         '[Dd]jango'                 'requirements*.txt'
detect "Django"         '[Dd]jango'                 'pyproject.toml'
detect "FastAPI"        '[Ff]ast[Aa][Pp][Ii]'       'requirements*.txt'
detect "FastAPI"        'fastapi'                   'pyproject.toml'
detect "Flask"          '[Ff]lask'                  'requirements*.txt'
detect "Spring Boot"    'spring-boot'               'pom.xml'
detect "Spring Boot"    'spring-boot'               'build.gradle*'
detect "ASP.NET Core"   'Microsoft.AspNetCore'      '*.csproj'
detect "EF Core"        'Microsoft.EntityFrameworkCore' '*.csproj'
detect "Rails"          "rails"                     'Gemfile'
detect "Go (gin/echo/chi/fiber)" 'gin-gonic|labstack/echo|go-chi|gofiber' 'go.mod'
detect "Flutter"        'flutter'                   'pubspec.yaml'

section "Routes / endpoints"
find_by_content '(Route::(get|post|put|patch|delete|resource|apiResource)|router\.(get|post|put|patch|delete)|app\.(get|post|put|patch|delete|Map(Get|Post|Put|Delete))\(|@(Get|Post|Put|Patch|Delete)(Mapping)?\(|@RequestMapping|\[Http(Get|Post|Put|Delete)|path\(|re_path\(|@(app|router|bp)\.(get|post|put|patch|delete|route)|createBrowserRouter|<Route |path: *.\/|resources? :|\.(GET|POST|PUT|DELETE)\()'

section "Frontend pages (file-based routing)"
find_by_path '/(app/.*/page\.(t|j)sx?|pages/.*\.(t|j)sx?|pages/.*\.vue|views/.*\.vue|Pages/.*\.razor)$'

section "Data models / entities / schema"
find_by_path '(/models?/|/entities/|/Entities/|/Domain/|\.entity\.ts$|models\.py$|schema\.prisma$|/schemas?/|DbContext\.cs$|db/schema\.rb$)'

section "Migrations / SQL"
find_by_path '(/migrations?/|/migrate/|db/migration|db/changelog|\.sql$)'

section "Roles / permissions / auth"
find_by_content '(hasRole|hasPermission|hasAnyRole|can\(|cannot\(|Gate::|authorize\(|@PreAuthorize|@Secured|@RolesAllowed|\[Authorize|AuthorizeView|@UseGuards|@Roles\(|permission_classes|has_perm|permission_required|requireRole|checkPermission|isAdmin|canActivate|role:|permission:|ROLE_|enum +Role|Roles? *= *\{|user\.role|\.roles\b|abilities|Ability)'

section "Policies / guards / middleware files"
find_by_path '(/[Pp]olicies/|/[Gg]uards?/|\.guard\.ts$|/[Mm]iddleware/|middleware\.(t|j)s$|permissions\.py$|ability\.(rb|ts|js)$|[Ss]ecurity[Cc]onfig)'

section "Validation (backend)"
find_by_content '(function rules\(|->validate\(|Validator::make|@IsNotEmpty|@IsString|@NotNull|@NotBlank|\[Required\]|AbstractValidator<|Joi\.object|body\(.*\)\.(notEmpty|isEmail)|serializers\.|class .*\(BaseModel\)|Field\(\.\.\.|validates? :|binding:"required|validate:"required|z\.object\(|yup\.object\(|Joi\.)'

section "Forms (frontend)"
find_by_content '(useForm\(|register\(|<Formik|validationSchema|z\.object\(|yup\.object\(|Validators\.required|FormBuilder|formGroup|<EditForm|<Form[ >]|Form\.Item|rules=|v-model|TextFormField)'

section "Enums / statuses (workflow candidates)"
find_by_content '(\benum\b|STATUS_|Status\.|status *[:=] *.[a-z_]+.|->enum\(|choices *=|TextChoices|IntegerChoices|@Enumerated)'

section "Services / business logic layers"
find_by_path '(/[Ss]ervices?/|/[Aa]ctions/|/[Uu]se[Cc]ases?/|/[Hh]andlers?/|/[Dd]omain/|\.service\.ts$|/[Rr]epositor(y|ies)/)'

section "Events / jobs / schedules / notifications"
find_by_content '(dispatch\(|ShouldQueue|@Scheduled|@Cron|@OnEvent|@EventListener|schedule\(|->daily\(|cron|celery|@shared_task|Notification|Mailable|sendMail|webhook|IHostedService|BackgroundService)'

section "Seeders / fixtures (default roles & data)"
find_by_path '(/seeders?/|/seeds?/|/fixtures?/|data\.sql$|seed\.(t|j)s$)'

section "Size"
printf 'Code files: '
find . -type f \( -name '*.php' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.vue' \
  -o -name '*.py' -o -name '*.java' -o -name '*.kt' -o -name '*.cs' -o -name '*.rb' -o -name '*.go' -o -name '*.dart' \) \
  -not -path '*/node_modules/*' -not -path '*/vendor/*' -not -path '*/.git/*' -not -path '*/dist/*' \
  -not -path '*/build/*' -not -path '*/.next/*' -not -path '*/target/*' -not -path '*/obj/*' 2>/dev/null | wc -l | tr -d ' '

echo
echo "(Lists are capped at $MAX per category; pass a larger number as the 2nd argument to see more.)"
