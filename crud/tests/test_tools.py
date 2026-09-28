"""تست ثبت ابزار User روی سرور MCP و پاکت JSON روی دیتابیس واقعی."""

from pathlib import Path
import asyncio
import os
import sys
import unittest
import uuid

from pydantic import ValidationError

_ROOT = Path(__file__).resolve().parent.parent
_REPO = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from errors.crud import (
    DATABASE_ERROR,
    INVALID_INPUT,
    PERMISSION_DENIED,
    PROJECT_NOT_FOUND,
    EXTERNAL_CONTACT_NOT_FOUND,
    CHAT_NOT_FOUND,
    MESSAGE_NOT_FOUND,
    NOTIFICATION_NOT_FOUND,
    AUDIT_LOG_NOT_FOUND,
    PERFORMANCE_ACTION_NOT_FOUND,
    CONTENT_NOT_FOUND,
    TEXT_ANALYSIS_NOT_FOUND,
    ISSUE_NOT_FOUND,
    TASK_FOLLOW_UP_NOT_FOUND,
    TASK_ITEM_NOT_FOUND,
    TASK_NOT_FOUND,
    QUERY_TIMEOUT,
    ROLE_NOT_FOUND,
    USER_NOT_FOUND,
    QueryTimeoutError,
    UserNotFoundError,
    format_error,
    format_success,
)
from mcp.server.mcpserver import MCPServer as FastMCP
from mcp_server.metadata import (
    DESTRUCTIVE_CRUD,
    READ_ONLY_CRUD,
    SERVER_NAME,
    SERVER_TITLE,
    TITLE_CREATE_USER,
    TITLE_DELETE_USER,
    TITLE_GET_USER,
    TITLE_LIST_USERS,
    TITLE_UPDATE_USER,
    TITLE_DELETE_PROJECT,
    TITLE_CREATE_TASK,
    TITLE_LIST_TASKS,
    TITLE_DELETE_TASK,
    TITLE_CREATE_TASK_ITEM,
    TITLE_LIST_TASK_ITEMS,
    TITLE_UPDATE_TASK_ITEM,
    TITLE_COMPLETE_TASK_ITEM,
    TITLE_DELETE_TASK_ITEM,
    TITLE_CREATE_EXTERNAL_CONTACT,
    TITLE_CREATE_CHAT,
    TITLE_CREATE_MESSAGE,
    TITLE_LIST_MESSAGES,
    TITLE_LIST_NOTIFICATIONS,
    TITLE_LIST_AUDIT_LOGS,
    TITLE_CREATE_PERFORMANCE_ACTION,
    TITLE_LIST_PERFORMANCE_ACTIONS,
    TITLE_CREATE_CONTENT,
    TITLE_GET_CONTENT,
    TITLE_LIST_CONTENTS,
    TITLE_DELETE_CONTENT,
    TITLE_SAVE_TEXT_ANALYSIS,
    TITLE_GET_TEXT_ANALYSIS,
    TITLE_LIST_TEXT_ANALYSES,
    TITLE_CREATE_ISSUE,
    TITLE_GET_ISSUE,
    TITLE_LIST_ISSUES,
    TITLE_LINK_ISSUE_CAUSE,
    TITLE_LINK_ISSUE_TASK,
    TITLE_SET_ISSUE_IMPORTANCE,
    TITLE_SET_ISSUE_URGENCY,
    TITLE_SET_ISSUE_SEVERITY,
    TITLE_ADD_ISSUE_IMPACT,
    TITLE_LINK_ISSUE_TOPIC,
    TITLE_LINK_ISSUE_ENTITY,
    WRITE_CRUD,
)
from mcp_server.register import register_crud_tools
from mcp_server.tools.permission.create_permission import run_create_permission
from mcp_server.tools.permission.list_permissions import run_list_permissions
from mcp_server.tools.role.create_role import run_create_role
from mcp_server.tools.role.delete_role import run_delete_role
from mcp_server.tools.role.get_role import run_get_role
from mcp_server.tools.role.list_roles import run_list_roles
from mcp_server.tools.role.update_role import run_update_role
from mcp_server.tools.role_permission.create_role_permission import (
    run_create_role_permission,
)
from mcp_server.tools.role_permission.delete_role_permission import (
    run_delete_role_permission,
)
from mcp_server.tools.user.create_user import run_create_user
from mcp_server.tools.user.delete_user import run_delete_user
from mcp_server.tools.user.get_user import run_get_user
from mcp_server.tools.user.list_assignable_users import run_list_assignable_users
from mcp_server.tools.user.list_users import run_list_users
from mcp_server.tools.user.update_user import run_update_user
from mcp_server.tools.user_role.create_user_role import run_create_user_role
from mcp_server.tools.user_role.delete_user_role import run_delete_user_role
from mcp_server.tools.user_role.list_user_roles import run_list_user_roles
from mcp_server.tools.project.create_project import run_create_project
from mcp_server.tools.project.delete_project import run_delete_project
from mcp_server.tools.project.get_project import run_get_project
from mcp_server.tools.project.list_projects import run_list_projects
from mcp_server.tools.project.update_project import run_update_project
from mcp_server.tools.project_member.create_project_member import (
    run_create_project_member,
)
from mcp_server.tools.project_member.list_project_members import (
    run_list_project_members,
)
from mcp_server.tools.project_member.update_project_member import (
    run_update_project_member,
)
from mcp_server.tools.task.create_task import run_create_task
from mcp_server.tools.task.delete_task import run_delete_task
from mcp_server.tools.task.get_task import run_get_task
from mcp_server.tools.task.list_tasks import run_list_tasks
from mcp_server.tools.task.update_task import run_update_task
from mcp_server.tools.task_item.complete_task_item import run_complete_task_item
from mcp_server.tools.task_item.create_task_item import run_create_task_item
from mcp_server.tools.task_item.delete_task_item import run_delete_task_item
from mcp_server.tools.task_item.list_task_items import run_list_task_items
from mcp_server.tools.task_item.update_task_item import run_update_task_item
from mcp_server.tools.task_follow_up.create_task_follow_up import (
    run_create_task_follow_up,
)
from mcp_server.tools.task_follow_up.get_task_follow_up import (
    run_get_task_follow_up,
)
from mcp_server.tools.task_follow_up.list_task_follow_ups import (
    run_list_task_follow_ups,
)
from mcp_server.tools.external_contact.create_external_contact import (
    run_create_external_contact,
)
from mcp_server.tools.external_contact.get_external_contact import (
    run_get_external_contact,
)
from mcp_server.tools.chat.create_chat import run_create_chat
from mcp_server.tools.chat.get_chat import run_get_chat
from mcp_server.tools.chat_member.create_chat_member import run_create_chat_member
from mcp_server.tools.chat_member.list_chat_members import run_list_chat_members
from mcp_server.tools.message.create_message import run_create_message
from mcp_server.tools.message.get_message import run_get_message
from mcp_server.tools.message.list_messages import run_list_messages
from mcp_server.tools.message_recipient.create_message_recipient import (
    run_create_message_recipient,
)
from mcp_server.tools.message_recipient.list_message_recipients import (
    run_list_message_recipients,
)
from mcp_server.tools.notification.get_notification import run_get_notification
from mcp_server.tools.notification.list_notifications import run_list_notifications
from mcp_server.tools.notification.mark_notification_read import (
    run_mark_notification_read,
)
from mcp_server.tools.audit_log.get_audit_log import run_get_audit_log
from mcp_server.tools.audit_log.list_audit_logs import run_list_audit_logs
from mcp_server.tools.performance_action.create_performance_action import (
    run_create_performance_action,
)
from mcp_server.tools.performance_action.get_performance_action import (
    run_get_performance_action,
)
from mcp_server.tools.performance_action.list_performance_actions import (
    run_list_performance_actions,
)
from mcp_server.tools.content.create_content import run_create_content
from mcp_server.tools.content.delete_content import run_delete_content
from mcp_server.tools.content.get_content import run_get_content
from mcp_server.tools.content.list_contents import run_list_contents
from mcp_server.tools.text_analysis.save_text_analysis import run_save_text_analysis
from mcp_server.tools.text_analysis.get_text_analysis import run_get_text_analysis
from mcp_server.tools.text_analysis.list_text_analyses import run_list_text_analyses
from mcp_server.tools.issue.create_issue import run_create_issue
from mcp_server.tools.issue.get_issue import run_get_issue
from mcp_server.tools.issue.list_issues import run_list_issues
from mcp_server.tools.issue.link_issue_cause import run_link_issue_cause
from mcp_server.tools.issue.link_issue_task import run_link_issue_task
from mcp_server.tools.issue.set_issue_importance import run_set_issue_importance
from mcp_server.tools.issue.set_issue_urgency import run_set_issue_urgency
from mcp_server.tools.issue.set_issue_severity import run_set_issue_severity
from mcp_server.tools.issue.add_issue_impact import run_add_issue_impact
from mcp_server.tools.issue.link_issue_topic import run_link_issue_topic
from mcp_server.tools.issue.link_issue_entity import run_link_issue_entity
from schemas.crud.user import ListUsersInput
from services.connection import open_connection
from repository import fetch_first, insert_row_on, run_query
from tests.conftest import (
    AuthorizedActorMixin,
    assign_seed_role,
    bind_actor_as_role,
    delete_temp_permission,
    delete_temp_project,
    delete_temp_role,
    delete_temp_task,
    delete_temp_issue,
    delete_temp_chat,
    delete_temp_external_contact,
    delete_temp_user,
    fetch_seed_permission_id,
    fetch_seed_role_id,
    insert_temp_account,
    delete_temp_account,
    insert_temp_user,
    minimal_user,
    unique_chat_title,
    unique_contact_name,
    unique_email,
    unique_permission_pair,
    unique_phone,
    unique_project_name,
    unique_role_name,
    unique_task_title,
    unique_issue_title,
    unique_task_item_title,
    unique_account_name,
    unique_storage_key,
)


_USER_TOOLS = {
    "create_user",
    "get_user",
    "list_users",
    "list_assignable_users",
    "update_user",
    "delete_user",
}
_REGISTERED_TOOLS = _USER_TOOLS | {
    "create_role",
    "get_role",
    "list_roles",
    "update_role",
    "delete_role",
    "create_permission",
    "list_permissions",
    "create_role_permission",
    "delete_role_permission",
    "list_role_permissions",
    "create_user_role",
    "delete_user_role",
    "list_user_roles",
    "create_project",
    "get_project",
    "list_projects",
    "update_project",
    "delete_project",
    "create_project_member",
    "list_project_members",
    "update_project_member",
    "create_task",
    "get_task",
    "list_tasks",
    "update_task",
    "delete_task",
    "create_task_item",
    "list_task_items",
    "update_task_item",
    "complete_task_item",
    "delete_task_item",
    "create_task_follow_up",
    "get_task_follow_up",
    "list_task_follow_ups",
    "create_external_contact",
    "get_external_contact",
    "list_external_contacts",
    "create_chat",
    "get_chat",
    "list_chats",
    "create_chat_member",
    "list_chat_members",
    "create_message",
    "get_message",
    "list_messages",
    "create_message_recipient",
    "list_message_recipients",
    "list_notifications",
    "get_notification",
    "mark_notification_read",
    "list_audit_logs",
    "get_audit_log",
    "create_performance_action",
    "get_performance_action",
    "list_performance_actions",
    "create_content",
    "get_content",
    "list_contents",
    "delete_content",
    "save_text_analysis",
    "get_text_analysis",
    "list_text_analyses",
    "create_issue",
    "get_issue",
    "list_issues",
    "link_issue_cause",
    "link_issue_task",
    "set_issue_importance",
    "set_issue_urgency",
    "set_issue_severity",
    "add_issue_impact",
    "link_issue_topic",
    "link_issue_entity",
}


class ServerPlumbingTests(unittest.TestCase):
    """ساخت سرور و ثبت ابزارهای User و نقش را بررسی می‌کند."""

    def test_metadata_names_management_crud(self) -> None:
        self.assertEqual(SERVER_NAME, "management-crud")
        self.assertEqual(SERVER_TITLE, "CRUD سامانه مدیریت")

    def test_register_adds_user_and_role_tools(self) -> None:
        mcp = FastMCP(name=SERVER_NAME)
        register_crud_tools(mcp)
        names = {tool.name for tool in mcp._tool_manager.list_tools()}
        self.assertEqual(names, _REGISTERED_TOOLS)
        self.assertTrue(_USER_TOOLS <= names)

    def test_server_module_lists_registered_tools(self) -> None:
        from mcp_server.server import mcp

        self.assertEqual(mcp.name, SERVER_NAME)
        names = {tool.name for tool in asyncio.run(mcp.list_tools())}
        self.assertEqual(names, _REGISTERED_TOOLS)


class ErrorEnvelopeTests(unittest.TestCase):
    def test_user_not_found_keeps_code(self) -> None:
        payload = format_error(UserNotFoundError("کاربر ۱ پیدا نشد"))
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], USER_NOT_FOUND)
        self.assertEqual(payload["message"], "کاربر ۱ پیدا نشد")

    def test_timeout_maps_to_query_timeout(self) -> None:
        payload = format_error(QueryTimeoutError("timeout"))
        self.assertEqual(payload["error_code"], QUERY_TIMEOUT)

    def test_pydantic_maps_to_invalid_input(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            ListUsersInput(limit="زیاد")
        payload = format_error(caught.exception)
        self.assertEqual(payload["error_code"], INVALID_INPUT)

    def test_unknown_maps_to_database_error(self) -> None:
        payload = format_error(RuntimeError("boom"))
        self.assertEqual(payload["error_code"], DATABASE_ERROR)
        self.assertEqual(payload["status"], "error")

    def test_success_envelope(self) -> None:
        payload = format_success("ثبت شد", id=7)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["message"], "ثبت شد")
        self.assertEqual(payload["id"], 7)


class CreateUserToolTests(AuthorizedActorMixin, unittest.TestCase):
    def test_tool_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        self.assertIn("create_user", by_name)
        tool = by_name["create_user"]
        self.assertEqual(tool.title, TITLE_CREATE_USER)
        self.assertIsNotNone(tool.annotations)
        self.assertFalse(tool.annotations.read_only_hint)
        self.assertEqual(
            tool.annotations.read_only_hint,
            WRITE_CRUD.read_only_hint,
        )
        schema = tool.input_schema
        required = set(schema.get("required") or [])
        self.assertEqual(required, {"first_name", "last_name", "username", "password"})
        properties = schema.get("properties") or {}
        self.assertNotIn("id", properties)
        self.assertNotIn("created_at", properties)
        self.assertNotIn("password_hash", properties)

    def test_run_success_envelope_then_cleanup(self) -> None:
        payload = run_create_user(**minimal_user())
        try:
            self.assertEqual(payload["status"], "success")
            self.assertIn("id", payload)
            self.assertNotIn("password", payload)
            self.assertNotIn("password_hash", payload)
        finally:
            delete_temp_user(payload["id"])

    def test_run_maps_empty_name_to_invalid_input(self) -> None:
        payload = run_create_user(**minimal_user(first_name="   "))
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], INVALID_INPUT)


class GetUserToolTests(AuthorizedActorMixin, unittest.TestCase):
    def test_tool_is_registered_as_readonly(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["get_user"]
        self.assertEqual(tool.title, TITLE_GET_USER)
        self.assertTrue(tool.annotations.read_only_hint)
        self.assertEqual(
            tool.annotations.read_only_hint,
            READ_ONLY_CRUD.read_only_hint,
        )
        properties = (tool.input_schema.get("properties") or {})
        self.assertEqual(set(properties), {"id"})

    def test_run_success_envelope_then_cleanup(self) -> None:
        new_id = insert_temp_user()
        try:
            payload = run_get_user(id=new_id)
            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["message"], "کاربر خوانده شد")
            self.assertEqual(payload["id"], new_id)
            self.assertEqual(payload["first_name"], "آزمایش")
            self.assertNotIn("password", payload)
            self.assertNotIn("password_hash", payload)
            self.assertNotIn("error_code", payload)
        finally:
            delete_temp_user(new_id)

    def test_run_maps_missing_row_to_user_not_found(self) -> None:
        new_id = insert_temp_user()
        delete_temp_user(new_id)
        payload = run_get_user(id=new_id)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], USER_NOT_FOUND)
        self.assertIn(str(new_id), payload["message"])


class ListUsersToolTests(AuthorizedActorMixin, unittest.TestCase):
    def test_tool_is_registered_as_readonly(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["list_users"]
        self.assertEqual(tool.title, TITLE_LIST_USERS)
        self.assertTrue(tool.annotations.read_only_hint)
        properties = tool.input_schema.get("properties") or {}
        self.assertEqual(set(properties), {"limit", "offset"})
        self.assertNotIn("id", properties)

    def test_run_returns_created_row_without_password_hash(self) -> None:
        payload = run_create_user(**minimal_user(last_name="فهرست‌ابزار"))
        new_id = payload["id"]
        try:
            listed = run_list_users(limit=50, offset=0)
            self.assertEqual(listed["status"], "success")
            self.assertEqual(listed["message"], "کاربران فهرست شدند")
            self.assertEqual(listed["limit"], 50)
            self.assertEqual(listed["offset"], 0)
            self.assertIsInstance(listed["records"], list)
            fetched_ids = {row["id"] for row in listed["records"]}
            self.assertIn(new_id, fetched_ids)
            for row in listed["records"]:
                self.assertNotIn("password", row)
                self.assertNotIn("password_hash", row)
        finally:
            delete_temp_user(new_id)

    def test_run_defaults_limit_ten_offset_zero(self) -> None:
        payload = run_list_users()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["limit"], 10)
        self.assertEqual(payload["offset"], 0)
        self.assertLessEqual(len(payload["records"]), 10)

    def test_run_maps_limit_above_fifty_to_invalid_input(self) -> None:
        payload = run_list_users(limit=51)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], INVALID_INPUT)
        self.assertNotIn("records", payload)


class UpdateUserToolTests(AuthorizedActorMixin, unittest.TestCase):
    def test_tool_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["update_user"]
        self.assertEqual(tool.title, TITLE_UPDATE_USER)
        self.assertFalse(tool.annotations.read_only_hint)
        self.assertFalse(tool.annotations.destructive_hint)
        self.assertEqual(
            tool.annotations.destructive_hint,
            WRITE_CRUD.destructive_hint,
        )
        required = set((tool.input_schema.get("required") or []))
        self.assertEqual(required, {"id"})
        properties = tool.input_schema.get("properties") or {}
        self.assertIn("password", properties)
        self.assertNotIn("password_hash", properties)
        self.assertNotIn("created_at", properties)

    def test_run_success_envelope_then_cleanup(self) -> None:
        new_id = insert_temp_user()
        try:
            payload = run_update_user(
                id=new_id,
                last_name="تهران",
                email=unique_email("upd"),
            )
            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["message"], "کاربر به‌روزرسانی شد")
            self.assertEqual(payload["id"], new_id)
            self.assertNotIn("error_code", payload)
            user = run_get_user(id=new_id)
            self.assertEqual(user["last_name"], "تهران")
            self.assertEqual(user["first_name"], "آزمایش")
        finally:
            delete_temp_user(new_id)

    def test_run_maps_missing_row_to_user_not_found(self) -> None:
        new_id = insert_temp_user()
        delete_temp_user(new_id)
        payload = run_update_user(id=new_id, last_name="نیست")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], USER_NOT_FOUND)


class DeleteUserToolTests(AuthorizedActorMixin, unittest.TestCase):
    def test_tool_is_registered_as_destructive(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["delete_user"]
        self.assertEqual(tool.title, TITLE_DELETE_USER)
        self.assertFalse(tool.annotations.read_only_hint)
        self.assertTrue(tool.annotations.destructive_hint)
        self.assertEqual(
            tool.annotations.destructive_hint,
            DESTRUCTIVE_CRUD.destructive_hint,
        )
        properties = tool.input_schema.get("properties") or {}
        self.assertEqual(set(properties), {"id"})

    def test_run_success_envelope_then_get_is_not_found(self) -> None:
        new_id = insert_temp_user()
        payload = run_delete_user(id=new_id)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["message"], "کاربر حذف شد")
        self.assertEqual(payload["id"], new_id)
        missing = run_get_user(id=new_id)
        self.assertEqual(missing["status"], "error")
        self.assertEqual(missing["error_code"], USER_NOT_FOUND)


class UserPermissionGateTests(unittest.TestCase):
    """دروازه User/Create و User/Read را روی ابزارهای User بررسی می‌کند."""

    def test_list_users_without_actor_is_denied(self) -> None:
        previous_id = os.environ.pop("MCP_ACTOR_USER_ID", None)
        previous_username = os.environ.pop("MCP_ACTOR_USERNAME", None)
        try:
            payload = run_list_users()
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["error_code"], PERMISSION_DENIED)
        finally:
            if previous_id is not None:
                os.environ["MCP_ACTOR_USER_ID"] = previous_id
            if previous_username is not None:
                os.environ["MCP_ACTOR_USERNAME"] = previous_username

    def test_user_role_without_create_cannot_create_user(self) -> None:
        actor = bind_actor_as_role("کاربر")
        try:
            payload = run_create_user(**minimal_user())
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["error_code"], PERMISSION_DENIED)
            self.assertIn("User/Create", payload["message"])
        finally:
            actor.close()

    def test_project_manager_cannot_grant_system_role(self) -> None:
        actor = bind_actor_as_role("مدیر پروژه")
        try:
            payload = run_create_user_role(
                user_id=actor.user_id,
                role_id=fetch_seed_role_id("کاربر"),
            )
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["error_code"], PERMISSION_DENIED)
        finally:
            actor.close()

    def test_assignable_users_hide_staff_from_project_manager(self) -> None:
        manager = bind_actor_as_role("مدیر پروژه")
        member_id = insert_temp_user(last_name="ثبت‌نام‌منتظر")
        staff_id = insert_temp_user(last_name="مدیر-دیگر")
        try:
            assign_seed_role(member_id, "کاربر")
            assign_seed_role(staff_id, "مدیر پروژه")
            listed = run_list_assignable_users(limit=50, offset=0)
            self.assertEqual(listed["status"], "success")
            ids = {row["id"] for row in listed["records"]}
            self.assertIn(member_id, ids)
            self.assertNotIn(staff_id, ids)
            self.assertNotIn(manager.user_id, ids)
        finally:
            delete_temp_user(staff_id)
            delete_temp_user(member_id)
            manager.close()

    def test_director_assignable_list_includes_staff(self) -> None:
        director = bind_actor_as_role("مدیر کل")
        staff_id = insert_temp_user(last_name="مدیر-دیده-شود")
        try:
            assign_seed_role(staff_id, "مدیر پروژه")
            listed = run_list_assignable_users(limit=50, offset=0)
            self.assertEqual(listed["status"], "success")
            ids = {row["id"] for row in listed["records"]}
            self.assertIn(staff_id, ids)
            self.assertIn(director.user_id, ids)
        finally:
            delete_temp_user(staff_id)
            director.close()

    def test_observer_can_list_users_but_not_create(self) -> None:
        actor = bind_actor_as_role("ناظر")
        try:
            listed = run_list_users(limit=10, offset=0)
            self.assertEqual(listed["status"], "success")
            created = run_create_user(**minimal_user())
            self.assertEqual(created["status"], "error")
            self.assertEqual(created["error_code"], PERMISSION_DENIED)
        finally:
            actor.close()


class RoleToolTests(unittest.TestCase):
    """ساخت و فهرست نقش و حفاظت نقش‌های seed را بررسی می‌کند."""

    def test_create_list_get_update_delete_custom_role(self) -> None:
        payload = run_create_role(name=unique_role_name(), description="موقت")
        role_id = payload["id"]
        try:
            self.assertEqual(payload["status"], "success")
            fetched = run_get_role(id=role_id)
            self.assertEqual(fetched["status"], "success")
            self.assertFalse(fetched["is_system_role"])
            listed = run_list_roles(limit=50, offset=0)
            ids = {row["id"] for row in listed["records"]}
            self.assertIn(role_id, ids)
            updated = run_update_role(id=role_id, description="ویرایش‌موقت")
            self.assertEqual(updated["status"], "success")
        finally:
            deleted = run_delete_role(id=role_id)
            self.assertEqual(deleted["status"], "success")

    def test_seed_roles_are_listed_and_not_deleted(self) -> None:
        listed = run_list_roles(limit=50, offset=0)
        names = {row["name"] for row in listed["records"]}
        self.assertIn("مدیر کل", names)
        self.assertIn("مدیر پروژه", names)
        self.assertIn("کاربر", names)
        admin_id = fetch_seed_role_id("مدیر کل")
        payload = run_delete_role(id=admin_id)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], INVALID_INPUT)
        still = run_get_role(id=admin_id)
        self.assertEqual(still["status"], "success")
        self.assertEqual(still["name"], "مدیر کل")
        self.assertTrue(still["is_system_role"])

    def test_system_role_name_cannot_change(self) -> None:
        admin_id = fetch_seed_role_id("مدیر کل")
        payload = run_update_role(id=admin_id, name="نام‌جعلی")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], INVALID_INPUT)
        still = run_get_role(id=admin_id)
        self.assertEqual(still["name"], "مدیر کل")

    def test_missing_role_is_not_found(self) -> None:
        payload = run_create_role(name=unique_role_name())
        role_id = payload["id"]
        run_delete_role(id=role_id)
        missing = run_get_role(id=role_id)
        self.assertEqual(missing["status"], "error")
        self.assertEqual(missing["error_code"], ROLE_NOT_FOUND)


class PermissionAndAssignmentToolTests(unittest.TestCase):
    """ساخت مجوز، دادن به نقش، و وصل کردن نقش به کاربر را بررسی می‌کند."""

    def test_create_and_list_permission(self) -> None:
        resource, action = unique_permission_pair()
        payload = run_create_permission(
            name=f"مجوز {resource}",
            resource=resource,
            action=action,
        )
        permission_id = payload["id"]
        try:
            self.assertEqual(payload["status"], "success")
            listed = run_list_permissions(limit=50, offset=0)
            ids = {row["id"] for row in listed["records"]}
            self.assertIn(permission_id, ids)
        finally:
            delete_temp_permission(permission_id)

    def test_assign_role_and_permission_then_user_can_list(self) -> None:
        role_payload = run_create_role(name=unique_role_name())
        role_id = role_payload["id"]
        permission_id = fetch_seed_permission_id("User", "Read")
        link = None
        user_id = insert_temp_user(last_name="دارای-خواندن")
        assignment = None
        admin = bind_actor_as_role("مدیر کل")
        try:
            link = run_create_role_permission(
                role_id=role_id,
                permission_id=permission_id,
            )
            self.assertEqual(link["status"], "success")
            assignment = run_create_user_role(user_id=user_id, role_id=role_id)
            self.assertEqual(assignment["status"], "success")
            roles = run_list_user_roles(user_id=user_id, limit=10, offset=0)
            self.assertEqual(len(roles["records"]), 1)
            self.assertEqual(roles["records"][0]["role_id"], role_id)
            os.environ["MCP_ACTOR_USER_ID"] = str(user_id)
            os.environ.pop("MCP_ACTOR_USERNAME", None)
            listed = run_list_users(limit=10, offset=0)
            self.assertEqual(listed["status"], "success")
            created = run_create_user(**minimal_user())
            self.assertEqual(created["status"], "error")
            self.assertEqual(created["error_code"], PERMISSION_DENIED)
            os.environ["MCP_ACTOR_USER_ID"] = str(admin.user_id)
            if assignment is not None and assignment.get("status") == "success":
                run_delete_user_role(id=assignment["id"])
                assignment = None
        finally:
            admin.close()
            delete_temp_user(user_id)
            if link is not None and link.get("status") == "success":
                run_delete_role_permission(id=link["id"])
            delete_temp_role(role_id)


class ProjectToolTests(unittest.TestCase):
    """ساخت پروژه، عضو شدن سازنده، و افزودن عضو دوم را بررسی می‌کند."""

    def test_create_inserts_row_and_adds_creator_as_manager(self) -> None:
        actor = bind_actor_as_role("مدیر پروژه")
        project_id = None
        try:
            payload = run_create_project(
                name=unique_project_name("طراحی‌سایت"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
                description="نمونه گام پنج",
            )
            self.assertEqual(payload["status"], "success")
            project_id = payload["id"]
            fetched = run_get_project(id=project_id)
            self.assertEqual(fetched["status"], "success")
            self.assertEqual(fetched["project_type_name"], "نرم‌افزاری")
            self.assertEqual(fetched["project_status_name"], "در حال اجرا")
            self.assertEqual(fetched["created_by"], actor.user_id)
            members = run_list_project_members(project_id=project_id, limit=10)
            self.assertEqual(members["status"], "success")
            self.assertEqual(len(members["records"]), 1)
            self.assertEqual(members["records"][0]["user_id"], actor.user_id)
            self.assertEqual(members["records"][0]["project_role_name"], "مدیر پروژه")
            self.assertTrue(members["records"][0]["is_active"])
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            actor.close()

    def test_add_second_member_with_member_role(self) -> None:
        actor = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="عضو")
        project_id = None
        try:
            created = run_create_project(
                name=unique_project_name("طراحی‌سایت"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            added = run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            self.assertEqual(added["status"], "success")
            members = run_list_project_members(project_id=project_id, limit=10)
            by_user = {row["user_id"]: row for row in members["records"]}
            self.assertEqual(set(by_user), {actor.user_id, reza_id})
            self.assertEqual(by_user[reza_id]["project_role_name"], "عضو")
            changed = run_update_project_member(
                id=by_user[reza_id]["id"],
                project_role="ناظر",
            )
            self.assertEqual(changed["status"], "success")
            members = run_list_project_members(project_id=project_id, limit=10)
            by_user = {row["user_id"]: row for row in members["records"]}
            self.assertEqual(by_user[reza_id]["project_role_name"], "ناظر")
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            actor.close()

    def test_update_project_changes_status(self) -> None:
        actor = bind_actor_as_role("مدیر پروژه")
        project_id = None
        try:
            created = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            updated = run_update_project(
                id=project_id,
                project_status="متوقف",
            )
            self.assertEqual(updated["status"], "success")
            fetched = run_get_project(id=project_id)
            self.assertEqual(fetched["project_status_name"], "متوقف")
            self.assertEqual(fetched["project_type_name"], "نرم‌افزاری")
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            actor.close()

    def test_missing_project_is_not_found(self) -> None:
        actor = bind_actor_as_role("مدیر پروژه")
        project_id = None
        try:
            created = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            delete_temp_project(project_id)
            missing = run_get_project(id=project_id)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], PROJECT_NOT_FOUND)
            project_id = None
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            actor.close()

    def test_user_role_cannot_create_project(self) -> None:
        actor = bind_actor_as_role("کاربر")
        try:
            payload = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["error_code"], PERMISSION_DENIED)
            self.assertIn("Project/Create", payload["message"])
        finally:
            actor.close()

    def test_delete_empty_project_then_get_is_not_found(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["delete_project"]
        self.assertEqual(tool.title, TITLE_DELETE_PROJECT)
        self.assertTrue(tool.annotations.destructive_hint)
        actor = bind_actor_as_role("مدیر پروژه")
        project_id = None
        try:
            created = run_create_project(
                name=unique_project_name("حذف-خالی"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            self.assertEqual(created["status"], "success")
            project_id = created["id"]
            deleted = run_delete_project(id=project_id)
            self.assertEqual(deleted["status"], "success")
            self.assertEqual(deleted["id"], project_id)
            missing = run_get_project(id=project_id)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], PROJECT_NOT_FOUND)
            project_id = None
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            actor.close()

    def test_delete_project_with_task_soft_cancels_project(self) -> None:
        actor = bind_actor_as_role("مدیر پروژه")
        project_id = None
        task_id = None
        try:
            created = run_create_project(
                name=unique_project_name("حذف-با-وظیفه"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            task = run_create_task(
                project_id=project_id,
                title=unique_task_title("مانع-حذف"),
                status="شروع نشده",
                priority="کم",
                importance="کم",
            )
            self.assertEqual(task["status"], "success")
            task_id = task["id"]
            deleted = run_delete_project(id=project_id)
            self.assertEqual(deleted["status"], "success")
            missing = run_get_project(id=project_id)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], PROJECT_NOT_FOUND)
            still_task = run_get_task(id=task_id)
            self.assertEqual(still_task["status"], "success")
            project_id = None
            task_id = None
        finally:
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            actor.close()

    def test_user_role_cannot_delete_project(self) -> None:
        owner = bind_actor_as_role("مدیر پروژه")
        project_id = None
        reza_id = insert_temp_user(first_name="رضا", last_name="بدون-حذف")
        assign_seed_role(reza_id, "کاربر")
        try:
            created = run_create_project(
                name=unique_project_name("حذف-بدون-مجوز"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            added = run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            self.assertEqual(added["status"], "success")
            previous_id = os.environ.get("MCP_ACTOR_USER_ID")
            previous_username = os.environ.get("MCP_ACTOR_USERNAME")
            os.environ["MCP_ACTOR_USER_ID"] = str(reza_id)
            os.environ.pop("MCP_ACTOR_USERNAME", None)
            try:
                denied = run_delete_project(id=project_id)
                self.assertEqual(denied["status"], "error")
                self.assertEqual(denied["error_code"], PERMISSION_DENIED)
            finally:
                if previous_id is None:
                    os.environ.pop("MCP_ACTOR_USER_ID", None)
                else:
                    os.environ["MCP_ACTOR_USER_ID"] = previous_id
                if previous_username is None:
                    os.environ.pop("MCP_ACTOR_USERNAME", None)
                else:
                    os.environ["MCP_ACTOR_USERNAME"] = previous_username
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            owner.close()


class ProjectScopeTests(unittest.TestCase):
    """محدودهٔ عضویت فعال: فهرست و ویرایش فقط پروژهٔ خود کاربر."""

    def test_list_projects_returns_only_own_memberships(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        ali_project = run_create_project(
            name=unique_project_name("مال‌علی"),
            project_type="نرم‌افزاری",
            project_status="در حال اجرا",
        )
        ali_project_id = ali_project["id"]
        reza_id = insert_temp_user(first_name="رضا", last_name="فهرست")
        assign_seed_role(reza_id, "کاربر")
        mohammad = None
        mohammad_project_id = None
        try:
            added = run_create_project_member(
                project_id=ali_project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            self.assertEqual(added["status"], "success")
            mohammad = bind_actor_as_role("مدیر پروژه")
            other = run_create_project(
                name=unique_project_name("مال‌محمد"),
                project_type="تحقیقاتی",
                project_status="در انتظار شروع",
            )
            mohammad_project_id = other["id"]
            listed = run_list_projects(limit=50, offset=0)
            ids = {row["id"] for row in listed["records"]}
            self.assertIn(mohammad_project_id, ids)
            self.assertNotIn(ali_project_id, ids)
            from tests.conftest import _restore_actor_env, _snapshot_actor_env

            previous = _snapshot_actor_env()
            try:
                import os

                os.environ["MCP_ACTOR_USER_ID"] = str(reza_id)
                os.environ.pop("MCP_ACTOR_USERNAME", None)
                reza_list = run_list_projects(limit=50, offset=0)
                reza_ids = {row["id"] for row in reza_list["records"]}
                self.assertIn(ali_project_id, reza_ids)
                self.assertNotIn(mohammad_project_id, reza_ids)
            finally:
                _restore_actor_env(previous)
        finally:
            if mohammad_project_id is not None:
                delete_temp_project(mohammad_project_id)
            if mohammad is not None:
                mohammad.close()
            delete_temp_project(ali_project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_director_sees_foreign_project_without_membership(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        created = run_create_project(
            name=unique_project_name("مال‌علی"),
            project_type="نرم‌افزاری",
            project_status="در حال اجرا",
        )
        project_id = created["id"]
        director = None
        try:
            director = bind_actor_as_role("مدیر کل")
            listed = run_list_projects(limit=50, offset=0)
            self.assertIn(project_id, {row["id"] for row in listed["records"]})
            fetched = run_get_project(id=project_id)
            self.assertEqual(fetched["status"], "success")
            self.assertEqual(fetched["id"], project_id)
        finally:
            if director is not None:
                director.close()
            delete_temp_project(project_id)
            ali.close()

    def test_member_lists_only_own_assigned_task(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="عضو")
        assign_seed_role(reza_id, "کاربر")
        project_id = None
        ali_task_id = None
        reza_task_id = None
        try:
            created = run_create_project(
                name=unique_project_name("تیم"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            ali_task = run_create_task(
                project_id=project_id,
                title=unique_task_title("کار-علی"),
                status="شروع نشده",
                priority="کم",
                importance="متوسط",
                assigned_to_user_id=ali.user_id,
            )
            ali_task_id = ali_task["id"]
            reza_task = run_create_task(
                project_id=project_id,
                title=unique_task_title("کار-رضا"),
                status="شروع نشده",
                priority="کم",
                importance="متوسط",
                assigned_to_user_id=reza_id,
            )
            reza_task_id = reza_task["id"]
            manager_ids = {row["id"] for row in run_list_tasks(project_id=project_id, limit=50)["records"]}
            self.assertIn(ali_task_id, manager_ids)
            self.assertIn(reza_task_id, manager_ids)
            from tests.conftest import _restore_actor_env, _snapshot_actor_env

            previous = _snapshot_actor_env()
            try:
                os.environ["MCP_ACTOR_USER_ID"] = str(reza_id)
                os.environ.pop("MCP_ACTOR_USERNAME", None)
                member_ids = {row["id"] for row in run_list_tasks(project_id=project_id, limit=50)["records"]}
                self.assertIn(reza_task_id, member_ids)
                self.assertNotIn(ali_task_id, member_ids)
            finally:
                _restore_actor_env(previous)
        finally:
            if ali_task_id is not None:
                delete_temp_task(ali_task_id)
            if reza_task_id is not None:
                delete_temp_task(reza_task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_outsider_with_update_cannot_change_foreign_project(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        created = run_create_project(
            name=unique_project_name("مال‌علی"),
            project_type="نرم‌افزاری",
            project_status="در حال اجرا",
        )
        project_id = created["id"]
        mohammad = None
        try:
            mohammad = bind_actor_as_role("مدیر پروژه")
            payload = run_update_project(id=project_id, description="نفوذ")
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["error_code"], PERMISSION_DENIED)
            still = None
            from tests.conftest import _restore_actor_env, _snapshot_actor_env
            import os

            previous = _snapshot_actor_env()
            try:
                os.environ["MCP_ACTOR_USER_ID"] = str(ali.user_id)
                os.environ.pop("MCP_ACTOR_USERNAME", None)
                still = run_get_project(id=project_id)
            finally:
                _restore_actor_env(previous)
            self.assertEqual(still["status"], "success")
            self.assertNotEqual(still.get("description"), "نفوذ")
        finally:
            if mohammad is not None:
                mohammad.close()
            delete_temp_project(project_id)
            ali.close()

    def test_member_user_cannot_update_without_project_update(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        created = run_create_project(
            name=unique_project_name(),
            project_type="نرم‌افزاری",
            project_status="در حال اجرا",
        )
        project_id = created["id"]
        reza_id = insert_temp_user(first_name="رضا", last_name="بدون‌ویرایش")
        assign_seed_role(reza_id, "کاربر")
        try:
            run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            import os
            from tests.conftest import _restore_actor_env, _snapshot_actor_env

            previous = _snapshot_actor_env()
            try:
                os.environ["MCP_ACTOR_USER_ID"] = str(reza_id)
                os.environ.pop("MCP_ACTOR_USERNAME", None)
                payload = run_update_project(id=project_id, description="نباید")
                self.assertEqual(payload["status"], "error")
                self.assertEqual(payload["error_code"], PERMISSION_DENIED)
                self.assertIn("Project/Update", payload["message"])
            finally:
                _restore_actor_env(previous)
        finally:
            delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()


class TaskToolTests(unittest.TestCase):
    """ساخت وظیفه روی پروژه، محدودهٔ فهرست، و جدا ماندن از پیگیری."""

    def test_create_assigns_active_member_and_outsider_cannot_list(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        ali_project = run_create_project(
            name=unique_project_name("سایت"),
            project_type="نرم‌افزاری",
            project_status="در حال اجرا",
        )
        ali_project_id = ali_project["id"]
        task_id = None
        mohammad = None
        mohammad_project_id = None
        try:
            created = run_create_task(
                project_id=ali_project_id,
                title="طراحی داشبورد",
                status="شروع نشده",
                priority="زیاد",
                importance="حیاتی",
                assigned_to_user_id=ali.user_id,
                due_date="2026-09-20",
            )
            self.assertEqual(created["status"], "success")
            task_id = created["id"]
            fetched = run_get_task(id=task_id)
            self.assertEqual(fetched["status"], "success")
            self.assertEqual(fetched["title"], "طراحی داشبورد")
            self.assertEqual(fetched["assigned_to_user_id"], ali.user_id)
            self.assertEqual(fetched["status_name"], "شروع نشده")
            self.assertEqual(fetched["priority_name"], "زیاد")
            self.assertEqual(fetched["importance_name"], "حیاتی")
            self.assertEqual(fetched["project_id"], ali_project_id)
            listed = run_list_tasks(project_id=ali_project_id, limit=50)
            self.assertEqual(listed["status"], "success")
            self.assertIn(task_id, {row["id"] for row in listed["records"]})
            mohammad = bind_actor_as_role("مدیر پروژه")
            other = run_create_project(
                name=unique_project_name("مال‌محمد"),
                project_type="تحقیقاتی",
                project_status="در انتظار شروع",
            )
            mohammad_project_id = other["id"]
            outsider_list = run_list_tasks(limit=50, offset=0)
            outsider_ids = {row["id"] for row in outsider_list["records"]}
            self.assertNotIn(task_id, outsider_ids)
            denied = run_list_tasks(project_id=ali_project_id, limit=50)
            self.assertEqual(denied["status"], "error")
            self.assertEqual(denied["error_code"], PERMISSION_DENIED)
            hidden = run_get_task(id=task_id)
            self.assertEqual(hidden["status"], "error")
            self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
        finally:
            if mohammad_project_id is not None:
                delete_temp_project(mohammad_project_id)
            if mohammad is not None:
                mohammad.close()
            if task_id is not None:
                delete_temp_task(task_id)
            delete_temp_project(ali_project_id)
            ali.close()

    def test_assignee_outside_project_is_invalid(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        stranger_id = insert_temp_user(first_name="غریبه", last_name="مسئول")
        project_id = None
        try:
            created = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            payload = run_create_task(
                project_id=project_id,
                title=unique_task_title(),
                status="شروع نشده",
                priority="کم",
                importance="کم",
                assigned_to_user_id=stranger_id,
            )
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["error_code"], INVALID_INPUT)
            self.assertIn("عضو فعال", payload["message"])
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(stranger_id)
            ali.close()

    def test_two_follow_ups_and_status_change_does_not_create_follow_up(
        self,
    ) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        created_project = run_create_project(
            name=unique_project_name("سایت"),
            project_type="نرم‌افزاری",
            project_status="در حال اجرا",
        )
        project_id = created_project["id"]
        task_id = None
        try:
            created = run_create_task(
                project_id=project_id,
                title="طراحی داشبورد",
                status="شروع نشده",
                priority="متوسط",
                importance="زیاد",
                assigned_to_user_id=ali.user_id,
            )
            task_id = created["id"]
            empty = run_list_task_follow_ups(task_id=task_id, limit=10)
            self.assertEqual(empty["status"], "success")
            self.assertEqual(empty["records"], [])
            call = run_create_task_follow_up(
                task_id=task_id,
                follow_up_type="تماس",
                status="منتظر پاسخ",
                note="۱۲ شهریور تماس گرفته شد",
                follow_up_date="2026-09-12T10:00:00",
            )
            self.assertEqual(call["status"], "success")
            message = run_create_task_follow_up(
                task_id=task_id,
                follow_up_type="پیام",
                status="پاسخ داده",
                note="۱۴ شهریور پیام ارسال شد",
                follow_up_date="2026-09-14T11:00:00",
            )
            self.assertEqual(message["status"], "success")
            listed = run_list_task_follow_ups(task_id=task_id, limit=10)
            self.assertEqual(listed["status"], "success")
            self.assertEqual(len(listed["records"]), 2)
            types = {row["follow_up_type_name"] for row in listed["records"]}
            self.assertEqual(types, {"تماس", "پیام"})
            fetched = run_get_task_follow_up(id=call["id"])
            self.assertEqual(fetched["status"], "success")
            self.assertEqual(fetched["follow_up_type_name"], "تماس")
            self.assertEqual(fetched["task_id"], task_id)
            from services.task_follow_up import count_task_follow_ups

            before = count_task_follow_ups(task_id)
            updated = run_update_task(id=task_id, status="در حال انجام")
            self.assertEqual(updated["status"], "success")
            after = count_task_follow_ups(task_id)
            self.assertEqual(after, before)
            self.assertEqual(after, 2)
            task = run_get_task(id=task_id)
            self.assertEqual(task["status_name"], "در حال انجام")
            still = run_list_task_follow_ups(task_id=task_id, limit=10)
            self.assertEqual(len(still["records"]), 2)
        finally:
            if task_id is not None:
                delete_temp_task(task_id)
            delete_temp_project(project_id)
            ali.close()

    def test_create_task_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["create_task"]
        self.assertEqual(tool.title, TITLE_CREATE_TASK)
        self.assertFalse(tool.annotations.read_only_hint)
        required = set(tool.input_schema.get("required") or [])
        self.assertIn("project_id", required)
        self.assertIn("title", required)
        properties = tool.input_schema.get("properties") or {}
        self.assertIn("priority", properties)
        self.assertIn("importance", properties)
        self.assertNotIn("created_by_user_id", properties)
        list_tool = by_name["list_tasks"]
        self.assertEqual(list_tool.title, TITLE_LIST_TASKS)
        self.assertTrue(list_tool.annotations.read_only_hint)
        delete_tool = by_name["delete_task"]
        self.assertEqual(delete_tool.title, TITLE_DELETE_TASK)
        self.assertTrue(delete_tool.annotations.destructive_hint)

    def test_delete_task_soft_cancel_then_get_is_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        task_id = None
        try:
            created = run_create_project(
                name=unique_project_name("حذف-وظیفه"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            task = run_create_task(
                project_id=project_id,
                title=unique_task_title("حذف-شو"),
                status="شروع نشده",
                priority="کم",
                importance="کم",
                assigned_to_user_id=ali.user_id,
            )
            self.assertEqual(task["status"], "success")
            task_id = task["id"]
            item = run_create_task_item(task_id=task_id, title="زیرکار حذف‌شونده")
            self.assertEqual(item["status"], "success")
            deleted = run_delete_task(id=task_id)
            self.assertEqual(deleted["status"], "success")
            self.assertEqual(deleted["id"], task_id)
            missing = run_get_task(id=task_id)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], TASK_NOT_FOUND)
            items = run_list_task_items(task_id=task_id)
            self.assertEqual(items["status"], "error")
            self.assertEqual(items["error_code"], TASK_NOT_FOUND)
            task_id = None
        finally:
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_outsider_cannot_delete_foreign_task(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        task_id = None
        mohammad = None
        try:
            created = run_create_project(
                name=unique_project_name("مال‌علی-حذف"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            task = run_create_task(
                project_id=project_id,
                title=unique_task_title("خارجی"),
                status="شروع نشده",
                priority="کم",
                importance="کم",
            )
            task_id = task["id"]
            mohammad = bind_actor_as_role("مدیر پروژه")
            denied = run_delete_task(id=task_id)
            self.assertEqual(denied["status"], "error")
            self.assertEqual(denied["error_code"], PERMISSION_DENIED)
            still = run_get_task(id=task_id)
            self.assertEqual(still["status"], "error")
            self.assertEqual(still["error_code"], PERMISSION_DENIED)
        finally:
            if mohammad is not None:
                mohammad.close()
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_member_user_can_create_task_but_not_follow_up(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="عضو")
        assign_seed_role(reza_id, "کاربر")
        project_id = None
        task_id = None
        try:
            created = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            import os
            from tests.conftest import _restore_actor_env, _snapshot_actor_env

            previous = _snapshot_actor_env()
            try:
                os.environ["MCP_ACTOR_USER_ID"] = str(reza_id)
                os.environ.pop("MCP_ACTOR_USERNAME", None)
                payload = run_create_task(
                    project_id=project_id,
                    title=unique_task_title("کار-رضا"),
                    status="شروع نشده",
                    priority="کم",
                    importance="متوسط",
                    assigned_to_user_id=reza_id,
                )
                self.assertEqual(payload["status"], "success")
                task_id = payload["id"]
                follow = run_create_task_follow_up(
                    task_id=task_id,
                    follow_up_type="تماس",
                    status="منتظر پاسخ",
                    note="نباید ثبت شود",
                )
                self.assertEqual(follow["status"], "error")
                self.assertEqual(follow["error_code"], PERMISSION_DENIED)
                self.assertIn("TaskFollowUp/Create", follow["message"])
            finally:
                _restore_actor_env(previous)
        finally:
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_missing_task_is_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        try:
            created = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            task = run_create_task(
                project_id=project_id,
                title=unique_task_title(),
                status="شروع نشده",
                priority="کم",
                importance="کم",
            )
            task_id = task["id"]
            delete_temp_task(task_id)
            missing = run_get_task(id=task_id)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], TASK_NOT_FOUND)
            follow = run_create_task_follow_up(
                task_id=task_id,
                follow_up_type="تماس",
                status="منتظر پاسخ",
                note="وظیفه نیست",
            )
            self.assertEqual(follow["status"], "error")
            self.assertEqual(follow["error_code"], TASK_NOT_FOUND)
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_missing_follow_up_is_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        missing = run_get_task_follow_up(id=9_999_999)
        try:
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], TASK_FOLLOW_UP_NOT_FOUND)
        finally:
            ali.close()


class MessageContactToolTests(unittest.TestCase):
    """مخاطب خارجی جدا از users، چت پروژه، XOR گیرنده، و پنهان بودن از غیرعضو."""

    def test_project_chat_message_to_member_and_external(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="عضو-چت")
        assign_seed_role(reza_id, "کاربر")
        project_id = None
        chat_id = None
        contact_id = None
        mohammad = None
        try:
            created_project = run_create_project(
                name=unique_project_name("سایت"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            self.assertEqual(created_project["status"], "success")
            project_id = created_project["id"]
            run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            phone = unique_phone()
            created_contact = run_create_external_contact(
                name=unique_contact_name("پیمانکار"),
                phone=phone,
            )
            self.assertEqual(created_contact["status"], "success")
            contact_id = created_contact["id"]
            fetched_contact = run_get_external_contact(id=contact_id)
            self.assertEqual(fetched_contact["status"], "success")
            self.assertEqual(fetched_contact["phone"], phone)
            connection = open_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM users WHERE phone = %s",
                        [phone],
                    )
                    self.assertIsNone(cursor.fetchone())
            finally:
                connection.close()
            created_chat = run_create_chat(
                title=unique_chat_title("پروژه"),
                chat_type="گفتگوی پروژه",
                project_id=project_id,
            )
            self.assertEqual(created_chat["status"], "success")
            chat_id = created_chat["id"]
            fetched_chat = run_get_chat(id=chat_id)
            self.assertEqual(fetched_chat["project_id"], project_id)
            self.assertEqual(fetched_chat["chat_type_name"], "گفتگوی پروژه")
            added = run_create_chat_member(chat_id=chat_id, user_id=reza_id)
            self.assertEqual(added["status"], "success")
            members = run_list_chat_members(chat_id=chat_id, limit=10)
            self.assertEqual(
                {row["user_id"] for row in members["records"]},
                {ali.user_id, reza_id},
            )
            task = run_create_task(
                project_id=project_id,
                title=unique_task_title("نظر"),
                status="شروع نشده",
                priority="متوسط",
                importance="متوسط",
                assigned_to_user_id=ali.user_id,
            )
            self.assertEqual(task["status"], "success")
            created_message = run_create_message(
                chat_id=chat_id,
                task_id=task["id"],
                text="پیگیری قرارداد را امروز انجام دهید.",
                recipient_user_id=reza_id,
                recipient_external_contact_id=contact_id,
            )
            self.assertEqual(created_message["status"], "success")
            message_id = created_message["id"]
            fetched_message = run_get_message(id=message_id)
            self.assertEqual(fetched_message["status"], "success")
            self.assertIn("پیگیری قرارداد", fetched_message["text"])
            self.assertEqual(fetched_message["task_id"], task["id"])
            self.assertNotIn("content_id", fetched_message)
            recipients = run_list_message_recipients(message_id=message_id, limit=10)
            self.assertEqual(recipients["status"], "success")
            self.assertEqual(len(recipients["records"]), 2)
            self.assertEqual(
                {
                    row["user_id"]
                    for row in recipients["records"]
                    if row["user_id"] is not None
                },
                {reza_id},
            )
            self.assertEqual(
                {
                    row["external_contact_id"]
                    for row in recipients["records"]
                    if row["external_contact_id"] is not None
                },
                {contact_id},
            )
            both = run_create_message_recipient(
                message_id=message_id,
                user_id=reza_id,
                external_contact_id=contact_id,
            )
            self.assertEqual(both["status"], "error")
            self.assertEqual(both["error_code"], INVALID_INPUT)
            neither = run_create_message_recipient(message_id=message_id)
            self.assertEqual(neither["status"], "error")
            self.assertEqual(neither["error_code"], INVALID_INPUT)
            missing = run_create_message(
                chat_id=chat_id,
                task_id=task["id"],
                text="بدون گیرنده",
            )
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], INVALID_INPUT)
            listed = run_list_messages(chat_id=chat_id, limit=50)
            self.assertIn(message_id, {row["id"] for row in listed["records"]})
            mohammad = bind_actor_as_role("مدیر پروژه")
            outsider_all = run_list_messages(limit=50, offset=0)
            self.assertNotIn(
                message_id,
                {row["id"] for row in outsider_all["records"]},
            )
            denied_chat = run_list_messages(chat_id=chat_id, limit=50)
            self.assertEqual(denied_chat["status"], "error")
            self.assertEqual(denied_chat["error_code"], PERMISSION_DENIED)
            hidden = run_get_message(id=message_id)
            self.assertEqual(hidden["status"], "error")
            self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
        finally:
            if mohammad is not None:
                mohammad.close()
            if chat_id is not None:
                delete_temp_chat(chat_id)
            if contact_id is not None:
                delete_temp_external_contact(contact_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_create_message_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        contact_tool = by_name["create_external_contact"]
        self.assertEqual(contact_tool.title, TITLE_CREATE_EXTERNAL_CONTACT)
        self.assertFalse(contact_tool.annotations.read_only_hint)
        self.assertIn("name", set(contact_tool.input_schema.get("required") or []))
        chat_tool = by_name["create_chat"]
        self.assertEqual(chat_tool.title, TITLE_CREATE_CHAT)
        self.assertNotIn(
            "created_by",
            (chat_tool.input_schema.get("properties") or {}),
        )
        message_tool = by_name["create_message"]
        self.assertEqual(message_tool.title, TITLE_CREATE_MESSAGE)
        self.assertFalse(message_tool.annotations.read_only_hint)
        required = set(message_tool.input_schema.get("required") or [])
        self.assertIn("chat_id", required)
        self.assertNotIn("task_id", required)
        self.assertIn("text", required)
        properties = message_tool.input_schema.get("properties") or {}
        self.assertIn("recipient_user_id", properties)
        self.assertIn("recipient_external_contact_id", properties)
        self.assertNotIn("content_id", properties)
        self.assertNotIn("sender_user_id", properties)
        list_tool = by_name["list_messages"]
        self.assertEqual(list_tool.title, TITLE_LIST_MESSAGES)
        self.assertTrue(list_tool.annotations.read_only_hint)
        recipient_tool = by_name["create_message_recipient"]
        recipient_props = recipient_tool.input_schema.get("properties") or {}
        self.assertIn("user_id", recipient_props)
        self.assertIn("external_contact_id", recipient_props)

    def test_member_user_can_send_message(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="فرستنده")
        assign_seed_role(reza_id, "کاربر")
        project_id = None
        chat_id = None
        try:
            created = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            chat = run_create_chat(
                title=unique_chat_title(),
                chat_type="گفتگوی پروژه",
                project_id=project_id,
            )
            chat_id = chat["id"]
            run_create_chat_member(chat_id=chat_id, user_id=reza_id)
            task = run_create_task(
                project_id=project_id,
                title=unique_task_title("رضا"),
                status="شروع نشده",
                priority="متوسط",
                importance="متوسط",
                assigned_to_user_id=reza_id,
            )
            self.assertEqual(task["status"], "success")
            from tests.conftest import _restore_actor_env, _snapshot_actor_env

            previous = _snapshot_actor_env()
            try:
                os.environ["MCP_ACTOR_USER_ID"] = str(reza_id)
                os.environ.pop("MCP_ACTOR_USERNAME", None)
                message = run_create_message(
                    chat_id=chat_id,
                    task_id=task["id"],
                    text="یادآوری جلسه فردا",
                    recipient_user_id=ali.user_id,
                )
                self.assertEqual(message["status"], "success")
                listed = run_list_messages(chat_id=chat_id, limit=50)
                self.assertIn(message["id"], {row["id"] for row in listed["records"]})
            finally:
                _restore_actor_env(previous)
        finally:
            if chat_id is not None:
                delete_temp_chat(chat_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_admin_can_message_anyone_in_private_chat(self) -> None:
        ali = bind_actor_as_role("مدیر کل")
        reza_id = insert_temp_user(first_name="رضا", last_name="خصوصی")
        assign_seed_role(reza_id, "کاربر")
        chat_id = None
        try:
            created = run_create_chat(
                title=unique_chat_title("خصوصی"),
                chat_type="گفتگوی خصوصی",
            )
            self.assertEqual(created["status"], "success")
            chat_id = created["id"]
            added = run_create_chat_member(chat_id=chat_id, user_id=reza_id)
            self.assertEqual(added["status"], "success")
            with_task = run_create_message(
                chat_id=chat_id,
                task_id=1,
                text="نباید تسک داشته باشد",
                recipient_user_id=reza_id,
            )
            self.assertEqual(with_task["status"], "error")
            self.assertEqual(with_task["error_code"], INVALID_INPUT)
            posted = run_create_message(
                chat_id=chat_id,
                text="سلام، وضعیت را بگویید.",
                recipient_user_id=reza_id,
            )
            self.assertEqual(posted["status"], "success")
            fetched = run_get_message(id=posted["id"])
            self.assertIsNone(fetched["task_id"])
            self.assertIn("سلام", fetched["text"])
            listed = run_list_messages(chat_id=chat_id, limit=20)
            self.assertIn(posted["id"], {row["id"] for row in listed["records"]})
        finally:
            if chat_id is not None:
                delete_temp_chat(chat_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_project_chat_message_can_omit_task(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        chat_id = None
        project_id = None
        try:
            created = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            chat = run_create_chat(
                title=unique_chat_title("پروژه"),
                chat_type="گفتگوی پروژه",
                project_id=project_id,
            )
            chat_id = chat["id"]
            posted = run_create_message(
                chat_id=chat_id,
                text="گزارش بدون وظیفه",
                recipient_user_id=ali.user_id,
            )
            self.assertEqual(posted["status"], "success")
            fetched = run_get_message(id=posted["id"])
            self.assertIsNone(fetched["task_id"])
            self.assertIn("گزارش بدون وظیفه", fetched["text"])
        finally:
            if chat_id is not None:
                delete_temp_chat(chat_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_missing_chat_and_message_are_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        missing_chat = run_get_chat(id=9_999_999)
        missing_message = run_get_message(id=9_999_999)
        missing_contact = run_get_external_contact(id=9_999_999)
        try:
            self.assertEqual(missing_chat["status"], "error")
            self.assertEqual(missing_chat["error_code"], CHAT_NOT_FOUND)
            self.assertEqual(missing_message["status"], "error")
            self.assertEqual(missing_message["error_code"], MESSAGE_NOT_FOUND)
            self.assertEqual(missing_contact["status"], "error")
            self.assertEqual(missing_contact["error_code"], EXTERNAL_CONTACT_NOT_FOUND)
        finally:
            ali.close()


class NotificationAuditToolTests(unittest.TestCase):
    """اعلان داخل پنل و ممیزی اثر جانبی ساخت وظیفه و عضو پروژه."""

    def test_create_task_notifies_assignee_and_writes_audit(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="مسئول")
        assign_seed_role(reza_id, "کاربر")
        project_id = None
        task_id = None
        note_id = None
        admin = None
        try:
            created = run_create_project(
                name=unique_project_name("اعلان"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            added = run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            self.assertEqual(added["status"], "success")
            created_task = run_create_task(
                project_id=project_id,
                title="طراحی صفحه",
                status="شروع نشده",
                priority="زیاد",
                importance="حیاتی",
                assigned_to_user_id=reza_id,
            )
            self.assertEqual(created_task["status"], "success")
            task_id = created_task["id"]
            from tests.conftest import _restore_actor_env, _snapshot_actor_env

            previous = _snapshot_actor_env()
            try:
                os.environ["MCP_ACTOR_USER_ID"] = str(reza_id)
                os.environ.pop("MCP_ACTOR_USERNAME", None)
                listed = run_list_notifications(limit=50, offset=0)
                self.assertEqual(listed["status"], "success")
                records = listed["records"]
                types = {row["notification_type_name"] for row in records}
                self.assertIn("وظیفه جدید", types)
                self.assertIn("افزوده شدن به پروژه", types)
                task_notes = [
                    row
                    for row in records
                    if row["notification_type_name"] == "وظیفه جدید"
                ]
                self.assertTrue(task_notes)
                self.assertIn("طراحی صفحه", task_notes[0]["message"])
                self.assertFalse(task_notes[0]["is_read"])
                note_id = task_notes[0]["id"]
                fetched = run_get_notification(id=note_id)
                self.assertEqual(fetched["status"], "success")
                self.assertEqual(fetched["id"], note_id)
                marked = run_mark_notification_read(id=note_id)
                self.assertEqual(marked["status"], "success")
                reread = run_get_notification(id=note_id)
                self.assertTrue(reread["is_read"])
            finally:
                _restore_actor_env(previous)
            ali_list = run_list_notifications(limit=50, offset=0)
            self.assertEqual(ali_list["status"], "success")
            ali_ids = {row["id"] for row in ali_list["records"]}
            self.assertNotIn(note_id, ali_ids)
            hidden = run_get_notification(id=note_id)
            self.assertEqual(hidden["status"], "error")
            self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
            updated = run_update_task(id=task_id, status="تکمیل شده")
            self.assertEqual(updated["status"], "success")
            admin = bind_actor_as_role("مدیر کل")
            audits = run_list_audit_logs(
                entity="Task",
                entity_id=task_id,
                limit=50,
            )
            self.assertEqual(audits["status"], "success")
            actions = {row["action"] for row in audits["records"]}
            self.assertIn("Create", actions)
            self.assertIn("Update", actions)
            created_rows = [
                row for row in audits["records"] if row["action"] == "Create"
            ]
            self.assertTrue(created_rows)
            self.assertEqual(created_rows[0]["entity"], "Task")
            self.assertEqual(created_rows[0]["new_value"]["title"], "طراحی صفحه")
            self.assertIsNone(created_rows[0]["old_value"])
            updated_rows = [
                row for row in audits["records"] if row["action"] == "Update"
            ]
            self.assertTrue(updated_rows)
            self.assertEqual(updated_rows[0]["old_value"]["status"], "شروع نشده")
            self.assertEqual(updated_rows[0]["new_value"]["status"], "تکمیل شده")
            fetched_audit = run_get_audit_log(id=created_rows[0]["id"])
            self.assertEqual(fetched_audit["status"], "success")
            member = bind_actor_as_role("کاربر")
            try:
                denied = run_list_audit_logs(limit=10)
                self.assertEqual(denied["status"], "error")
                self.assertEqual(denied["error_code"], PERMISSION_DENIED)
                self.assertIn("AuditLog/Read", denied["message"])
            finally:
                member.close()
        finally:
            if admin is not None:
                admin.close()
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_notification_and_audit_tools_are_registered(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        names = {tool.name for tool in tools}
        self.assertIn("list_notifications", names)
        self.assertIn("get_notification", names)
        self.assertIn("mark_notification_read", names)
        self.assertIn("list_audit_logs", names)
        self.assertIn("get_audit_log", names)
        self.assertNotIn("create_notification", names)
        self.assertNotIn("create_audit_log", names)
        by_name = {tool.name: tool for tool in tools}
        self.assertEqual(by_name["list_notifications"].title, TITLE_LIST_NOTIFICATIONS)
        self.assertTrue(by_name["list_notifications"].annotations.read_only_hint)
        self.assertFalse(by_name["mark_notification_read"].annotations.read_only_hint)
        self.assertEqual(by_name["list_audit_logs"].title, TITLE_LIST_AUDIT_LOGS)
        self.assertTrue(by_name["list_audit_logs"].annotations.read_only_hint)

    def test_missing_notification_and_audit_are_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر کل")
        try:
            missing_note = run_get_notification(id=9_999_999)
            missing_audit = run_get_audit_log(id=9_999_999)
            self.assertEqual(missing_note["status"], "error")
            self.assertEqual(missing_note["error_code"], NOTIFICATION_NOT_FOUND)
            self.assertEqual(missing_audit["status"], "error")
            self.assertEqual(missing_audit["error_code"], AUDIT_LOG_NOT_FOUND)
        finally:
            ali.close()


class PerformanceActionToolTests(unittest.TestCase):
    """تشویق و تنبیه جدا از کاربر و مالی؛ امتیاز و مبلغ ستون جدا."""

    def test_performance_tools_are_registered_without_score_tools(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        names = {tool.name for tool in tools}
        self.assertIn("create_performance_action", names)
        self.assertIn("get_performance_action", names)
        self.assertIn("list_performance_actions", names)
        self.assertNotIn("create_performance_score", names)
        self.assertNotIn("list_performance_action_types", names)
        by_name = {tool.name: tool for tool in tools}
        create_tool = by_name["create_performance_action"]
        self.assertEqual(create_tool.title, TITLE_CREATE_PERFORMANCE_ACTION)
        self.assertFalse(create_tool.annotations.read_only_hint)
        self.assertEqual(
            create_tool.annotations.read_only_hint,
            WRITE_CRUD.read_only_hint,
        )
        required = set(create_tool.input_schema.get("required") or [])
        self.assertIn("user_id", required)
        self.assertIn("reason", required)
        properties = create_tool.input_schema.get("properties") or {}
        self.assertIn("action_type", properties)
        self.assertIn("score", properties)
        self.assertIn("amount", properties)
        self.assertIn("account_id", properties)
        list_tool = by_name["list_performance_actions"]
        self.assertEqual(list_tool.title, TITLE_LIST_PERFORMANCE_ACTIONS)
        self.assertTrue(list_tool.annotations.read_only_hint)

    def test_appreciation_cash_reward_warning_and_score_sum(self) -> None:
        from services.performance_action import score_totals_for_user

        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="تأخیر")
        assign_seed_role(reza_id, "کاربر")
        project_id = None
        account_id = None
        member = None
        try:
            created_project = run_create_project(
                name=unique_project_name("عملکرد"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            self.assertEqual(created_project["status"], "success")
            project_id = created_project["id"]
            run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            account_id = insert_temp_account(unique_account_name("صندوق پاداش"))
            before_tx = _count_user_transactions(ali.user_id)

            praise = run_create_performance_action(
                user_id=ali.user_id,
                project_id=project_id,
                action_type="تقدیر",
                reason="تحویل به‌موقع طراحی",
                score=10,
            )
            self.assertEqual(praise["status"], "success")
            praised = run_get_performance_action(id=praise["id"])
            self.assertEqual(praised["status"], "success")
            self.assertEqual(praised["score"], 10)
            self.assertIsNone(praised["amount"])
            self.assertIsNone(praised["financial_transaction_id"])
            self.assertEqual(praised["type_name"], "تقدیر")
            self.assertEqual(praised["type_category"], "REWARD")
            self.assertEqual(_count_user_transactions(ali.user_id), before_tx)

            bonus = run_create_performance_action(
                user_id=ali.user_id,
                project_id=project_id,
                action_type="پاداش نقدی",
                reason="تحویل به‌موقع و کیفیت",
                score=10,
                amount=2_000_000,
                account_id=account_id,
            )
            self.assertEqual(bonus["status"], "success")
            cashed = run_get_performance_action(id=bonus["id"])
            self.assertEqual(cashed["status"], "success")
            self.assertEqual(cashed["score"], 10)
            self.assertEqual(cashed["amount"], 2_000_000)
            self.assertIsNotNone(cashed["financial_transaction_id"])
            tx = _fetch_transaction(cashed["financial_transaction_id"])
            self.assertEqual(tx["name"], "پاداش")
            self.assertEqual(tx["amount"], -2_000_000)
            self.assertEqual(tx["account_id"], account_id)
            self.assertEqual(_count_user_transactions(ali.user_id), before_tx + 1)

            warning = run_create_performance_action(
                user_id=reza_id,
                project_id=project_id,
                action_type="اخطار",
                reason="تأخیر در تحویل",
                score=-5,
            )
            self.assertEqual(warning["status"], "success")
            warned = run_get_performance_action(id=warning["id"])
            self.assertEqual(warned["score"], -5)
            self.assertIsNone(warned["amount"])
            self.assertIsNone(warned["financial_transaction_id"])
            self.assertEqual(_count_user_transactions(reza_id), 0)

            listed = run_list_performance_actions(
                user_id=ali.user_id,
                project_id=project_id,
                limit=50,
            )
            self.assertEqual(listed["status"], "success")
            records = listed["records"]
            self.assertEqual(len(records), 2)
            by_type = {row["type_name"]: row for row in records}
            self.assertIn("تقدیر", by_type)
            self.assertIn("پاداش نقدی", by_type)
            self.assertEqual(by_type["تقدیر"]["score"], 10)
            self.assertIsNone(by_type["تقدیر"]["amount"])
            self.assertEqual(by_type["پاداش نقدی"]["score"], 10)
            self.assertEqual(by_type["پاداش نقدی"]["amount"], 2_000_000)
            self.assertNotIn("اخطار", by_type)

            ali_totals = score_totals_for_user(ali.user_id)
            self.assertEqual(ali_totals["scores_total"], 20)
            self.assertEqual(ali_totals["actions_total"], 20)
            reza_totals = score_totals_for_user(reza_id)
            self.assertEqual(reza_totals["scores_total"], -5)
            self.assertEqual(reza_totals["actions_total"], -5)

            no_reason = run_create_performance_action(
                user_id=ali.user_id,
                action_type="تقدیر",
                reason="   ",
                score=1,
            )
            self.assertEqual(no_reason["status"], "error")
            self.assertEqual(no_reason["error_code"], INVALID_INPUT)

            no_account = run_create_performance_action(
                user_id=ali.user_id,
                action_type="پاداش نقدی",
                reason="بدون حساب",
                amount=1000,
            )
            self.assertEqual(no_account["status"], "error")
            self.assertEqual(no_account["error_code"], INVALID_INPUT)

            member = bind_actor_as_role("کاربر")
            denied = run_create_performance_action(
                user_id=reza_id,
                action_type="تقدیر",
                reason="بدون مجوز",
                score=1,
            )
            self.assertEqual(denied["status"], "error")
            self.assertEqual(denied["error_code"], PERMISSION_DENIED)
            self.assertIn("Performance/Create", denied["message"])
        finally:
            if member is not None:
                member.close()
            if project_id is not None:
                delete_temp_project(project_id)
            if account_id is not None:
                delete_temp_account(account_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_missing_performance_action_is_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر کل")
        try:
            missing = run_get_performance_action(id=9_999_999)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], PERFORMANCE_ACTION_NOT_FOUND)
        finally:
            ali.close()


class TaskItemToolTests(unittest.TestCase):
    """زیرکار تو در تو، تیک، قید مسئول، CASCADE و sort_order."""

    def test_task_item_tools_are_registered(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        create_tool = by_name["create_task_item"]
        self.assertEqual(create_tool.title, TITLE_CREATE_TASK_ITEM)
        self.assertFalse(create_tool.annotations.read_only_hint)
        required = set(create_tool.input_schema.get("required") or [])
        self.assertIn("task_id", required)
        self.assertIn("title", required)
        properties = create_tool.input_schema.get("properties") or {}
        self.assertIn("parent_item_id", properties)
        self.assertIn("start_date", properties)
        self.assertIn("end_date", properties)
        self.assertNotIn("created_by_user_id", properties)
        list_tool = by_name["list_task_items"]
        self.assertEqual(list_tool.title, TITLE_LIST_TASK_ITEMS)
        self.assertTrue(list_tool.annotations.read_only_hint)
        self.assertEqual(by_name["update_task_item"].title, TITLE_UPDATE_TASK_ITEM)
        complete_tool = by_name["complete_task_item"]
        self.assertEqual(complete_tool.title, TITLE_COMPLETE_TASK_ITEM)
        self.assertFalse(complete_tool.annotations.destructive_hint)
        delete_tool = by_name["delete_task_item"]
        self.assertEqual(delete_tool.title, TITLE_DELETE_TASK_ITEM)
        self.assertTrue(delete_tool.annotations.destructive_hint)

    def test_assignee_nested_items_complete_member_denied_cascade_and_order(
        self,
    ) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        reza_id = insert_temp_user(first_name="رضا", last_name="عضو")
        assign_seed_role(reza_id, "مدیر پروژه")
        project_id = None
        task_id = None
        try:
            created_project = run_create_project(
                name=unique_project_name("سایت"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created_project["id"]
            run_create_project_member(
                project_id=project_id,
                user_id=reza_id,
                project_role="عضو",
            )
            created_task = run_create_task(
                project_id=project_id,
                title="طراحی داشبورد",
                status="شروع نشده",
                priority="زیاد",
                importance="حیاتی",
                assigned_to_user_id=ali.user_id,
            )
            self.assertEqual(created_task["status"], "success")
            task_id = created_task["id"]
            later = run_create_task_item(
                task_id=task_id,
                title="وایر فریم دیر",
                sort_order=5,
                start_date="2026-09-20",
                end_date="2026-09-22",
            )
            self.assertEqual(later["status"], "success")
            parent = run_create_task_item(
                task_id=task_id,
                title="وایر فریم",
                sort_order=1,
                start_date="2026-09-18",
                end_date="2026-09-21",
            )
            self.assertEqual(parent["status"], "success")
            child = run_create_task_item(
                task_id=task_id,
                title="نسخه موبایل",
                parent_item_id=parent["id"],
                sort_order=0,
            )
            self.assertEqual(child["status"], "success")
            ticked = run_complete_task_item(id=child["id"])
            self.assertEqual(ticked["status"], "success")
            listed = run_list_task_items(task_id=task_id)
            self.assertEqual(listed["status"], "success")
            titles = [row["title"] for row in listed["records"]]
            self.assertEqual(titles[:2], ["وایر فریم", "وایر فریم دیر"])
            by_id = {row["id"]: row for row in listed["records"]}
            self.assertTrue(by_id[child["id"]]["is_completed"])
            self.assertIsNotNone(by_id[child["id"]]["completed_at"])
            self.assertEqual(by_id[child["id"]]["completed_by_user_id"], ali.user_id)
            self.assertEqual(by_id[parent["id"]]["start_date"], "2026-09-18")
            self.assertEqual(by_id[parent["id"]]["end_date"], "2026-09-21")
            tree_titles = [node["title"] for node in listed["tree"]]
            self.assertEqual(tree_titles, ["وایر فریم", "وایر فریم دیر"])
            self.assertEqual(
                [node["title"] for node in listed["tree"][0]["children"]],
                ["نسخه موبایل"],
            )
            connection = open_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM reminders WHERE task_item_id = %s",
                        [parent["id"]],
                    )
                    reminder_count = cursor.fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(reminder_count, 0)

            import os
            from tests.conftest import _restore_actor_env, _snapshot_actor_env

            previous = _snapshot_actor_env()
            try:
                os.environ["MCP_ACTOR_USER_ID"] = str(reza_id)
                os.environ.pop("MCP_ACTOR_USERNAME", None)
                denied_update = run_update_task_item(
                    id=parent["id"],
                    title="نباید عوض شود",
                )
                self.assertEqual(denied_update["status"], "error")
                self.assertEqual(denied_update["error_code"], PERMISSION_DENIED)
                self.assertIn("مسئول", denied_update["message"])
                self.assertNotEqual(denied_update["error_code"], DATABASE_ERROR)
                denied_complete = run_complete_task_item(id=parent["id"])
                self.assertEqual(denied_complete["status"], "error")
                self.assertEqual(denied_complete["error_code"], PERMISSION_DENIED)
                member_list = run_list_task_items(task_id=task_id)
                self.assertEqual(member_list["status"], "success")
                self.assertEqual(len(member_list["records"]), 3)
            finally:
                _restore_actor_env(previous)

            deleted = run_delete_task_item(id=parent["id"])
            self.assertEqual(deleted["status"], "success")
            after_delete = run_list_task_items(task_id=task_id)
            remaining_ids = {row["id"] for row in after_delete["records"]}
            self.assertNotIn(parent["id"], remaining_ids)
            self.assertNotIn(child["id"], remaining_ids)
            self.assertIn(later["id"], remaining_ids)
            missing_child = run_complete_task_item(id=child["id"])
            self.assertEqual(missing_child["status"], "error")
            self.assertEqual(missing_child["error_code"], TASK_ITEM_NOT_FOUND)
        finally:
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            delete_temp_user(reza_id)
            ali.close()

    def test_missing_task_item_is_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            missing = run_update_task_item(id=9_999_999, title=unique_task_item_title())
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], TASK_ITEM_NOT_FOUND)
        finally:
            ali.close()

    def test_unassigned_task_cannot_get_items(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        task_id = None
        try:
            created_project = run_create_project(
                name=unique_project_name(),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created_project["id"]
            created_task = run_create_task(
                project_id=project_id,
                title=unique_task_title(),
                status="شروع نشده",
                priority="کم",
                importance="کم",
            )
            task_id = created_task["id"]
            payload = run_create_task_item(
                task_id=task_id,
                title=unique_task_item_title(),
            )
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["error_code"], PERMISSION_DENIED)
            self.assertIn("مسئول", payload["message"])
        finally:
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()


class ContentToolTests(unittest.TestCase):
    """ثبت متن و متادیتای صوت در contents را روی Postgres می‌سنجد."""

    def test_create_content_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["create_content"]
        self.assertEqual(tool.title, TITLE_CREATE_CONTENT)
        self.assertFalse(tool.annotations.read_only_hint)
        properties = tool.input_schema.get("properties") or {}
        self.assertIn("content_kind", properties)
        self.assertIn("text_body", properties)
        self.assertIn("storage_key", properties)
        get_tool = by_name["get_content"]
        self.assertEqual(get_tool.title, TITLE_GET_CONTENT)
        self.assertTrue(get_tool.annotations.read_only_hint)
        list_tool = by_name["list_contents"]
        self.assertEqual(list_tool.title, TITLE_LIST_CONTENTS)
        self.assertTrue(list_tool.annotations.read_only_hint)
        delete_tool = by_name["delete_content"]
        self.assertEqual(delete_tool.title, TITLE_DELETE_CONTENT)
        self.assertTrue(delete_tool.annotations.destructive_hint)

    def test_text_and_voice_content_roundtrip(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            text = run_create_content(
                content_kind="TEXT",
                text_body="خلاصه جلسه تیم: داشبورد تا چهارشنبه.",
            )
            self.assertEqual(text["status"], "success")
            loaded = run_get_content(id=text["id"])
            self.assertEqual(loaded["content_kind_code"], "TEXT")
            self.assertIn("داشبورد", loaded["text_body"])
            self.assertIsNone(loaded["media_file_id"])

            voice = run_create_content(
                content_kind="VOICE",
                storage_key=unique_storage_key(),
                original_filename="meeting.ogg",
                mime_type="audio/ogg",
                file_size_bytes=2048,
                duration_seconds=90,
                text_body="caption صوت",
            )
            self.assertEqual(voice["status"], "success")
            audio = run_get_content(id=voice["id"])
            self.assertEqual(audio["content_kind_code"], "VOICE")
            self.assertEqual(audio["original_filename"], "meeting.ogg")
            self.assertEqual(audio["file_size_bytes"], 2048)

            empty = run_create_content(content_kind="TEXT", text_body="  ")
            self.assertEqual(empty["status"], "error")
            self.assertEqual(empty["error_code"], INVALID_INPUT)

            image = run_create_content(content_kind="IMAGE")
            self.assertEqual(image["status"], "error")
            self.assertEqual(image["error_code"], INVALID_INPUT)

            listed = run_list_contents()
            self.assertEqual(listed["status"], "success")
            self.assertTrue(any(row["id"] == text["id"] for row in listed["records"]))

            removed = run_delete_content(id=text["id"])
            self.assertEqual(removed["status"], "success")
            gone = run_get_content(id=text["id"])
            self.assertEqual(gone["status"], "error")
            self.assertEqual(gone["error_code"], CONTENT_NOT_FOUND)
            listed_after = run_list_contents()
            self.assertFalse(any(row["id"] == text["id"] for row in listed_after["records"]))
        finally:
            ali.close()

    def test_missing_content_is_not_found(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            missing = run_get_content(id=9_999_999)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], CONTENT_NOT_FOUND)
        finally:
            ali.close()


class TextAnalysisToolTests(unittest.TestCase):
    """ذخیره خروجی NER با وضعیت پیشنهادی و باقی‌ماندن نمایش."""

    def test_save_text_analysis_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["save_text_analysis"]
        self.assertEqual(tool.title, TITLE_SAVE_TEXT_ANALYSIS)
        self.assertFalse(tool.annotations.read_only_hint)
        required = set(tool.input_schema.get("required") or [])
        self.assertIn("source_type", required)
        properties = tool.input_schema.get("properties") or {}
        self.assertIn("mentions", properties)
        self.assertIn("topics", properties)
        self.assertIn("discourses", properties)
        self.assertIn("intents", properties)
        self.assertIn("rhetorics", properties)
        self.assertIn("facts", properties)
        self.assertIn("quotes", properties)
        self.assertNotIn("created_by_user_id", properties)
        get_tool = by_name["get_text_analysis"]
        self.assertEqual(get_tool.title, TITLE_GET_TEXT_ANALYSIS)
        self.assertTrue(get_tool.annotations.read_only_hint)
        list_tool = by_name["list_text_analyses"]
        self.assertEqual(list_tool.title, TITLE_LIST_TEXT_ANALYSES)
        self.assertTrue(list_tool.annotations.read_only_hint)

    def test_save_report_analysis_keeps_display_payload(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        try:
            created = run_create_project(
                name=unique_project_name("تحلیل"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            chat = run_create_chat(
                title=unique_chat_title("تحلیل"),
                chat_type="گفتگوی پروژه",
                project_id=project_id,
            )
            task = run_create_task(
                project_id=project_id,
                title=unique_task_title("تحلیل"),
                status="شروع نشده",
                priority="متوسط",
                importance="متوسط",
                assigned_to_user_id=ali.user_id,
            )
            body = "سارا احمدی از واحد مالی تأخیر پرداخت پیمانکار را گزارش کرد."
            posted = run_create_message(
                chat_id=chat["id"],
                task_id=task["id"],
                text=body,
                recipient_user_id=ali.user_id,
            )
            self.assertEqual(posted["status"], "success")
            saved = run_save_text_analysis(
                source_type="message",
                source_id=posted["id"],
                model="test-ner",
                mentions=[
                    {
                        "type": "PERSON",
                        "canonical_name": "سارا احمدی",
                        "normalized_name": f"سارا احمدی {posted['id']}",
                        "mention_text": "سارا احمدی",
                        "start_offset": 0,
                        "end_offset": 10,
                        "confidence": 0.91,
                    },
                    {
                        "type": "UNIT",
                        "canonical_name": "واحد مالی",
                        "normalized_name": f"واحد مالی {posted['id']}",
                        "mention_text": "واحد مالی",
                        "start_offset": 15,
                        "end_offset": 24,
                        "confidence": 0.88,
                    },
                ],
                keywords=[
                    {
                        "phrase": "تأخیر پرداخت",
                        "mention_text": "تأخیر پرداخت",
                        "start_offset": 26,
                        "end_offset": 38,
                        "confidence": 0.8,
                    }
                ],
                topics=[
                    {
                        "code": "finance.payment.delay",
                        "is_primary": True,
                        "confidence": 0.8,
                        "mention_text": "تأخیر پرداخت",
                    }
                ],
                sentiment={
                    "polarity": "negative",
                    "intensity": "medium",
                    "mention_text": "تأخیر پرداخت پیمانکار",
                },
                emotions=[
                    {
                        "emotion": "worry",
                        "intensity": "medium",
                        "mention_text": "تأخیر پرداخت",
                    }
                ],
                discourses=[
                    {
                        "code": "issue",
                        "is_primary": True,
                        "confidence": 0.9,
                        "mention_text": "تأخیر پرداخت پیمانکار",
                    },
                    {
                        "code": "request",
                        "is_primary": False,
                        "confidence": 0.7,
                        "mention_text": "گزارش کرد",
                    },
                ],
                intents=[
                    {
                        "code": "report_problem",
                        "is_primary": True,
                        "confidence": 0.85,
                        "mention_text": "تأخیر پرداخت پیمانکار را گزارش کرد",
                        "slots": {
                            "گزارش‌دهنده": "سارا احمدی",
                            "مسئله": "تأخیر پرداخت پیمانکار",
                        },
                    }
                ],
                rhetorics=[
                    {
                        "code": "literal",
                        "is_primary": True,
                        "confidence": 0.8,
                        "mention_text": "تأخیر پرداخت پیمانکار",
                        "intended_meaning": "تأخیر پرداخت پیمانکار گزارش شد",
                        "slots": {"محتوا": "تأخیر پرداخت پیمانکار"},
                    }
                ],
            )
            self.assertEqual(saved["status"], "success")
            self.assertEqual(saved["source_type"], "message")
            self.assertEqual(saved["source_id"], posted["id"])
            self.assertEqual(saved["project_id"], project_id)
            self.assertEqual(saved["mention_count"], 2)
            self.assertEqual(saved["keyword_count"], 1)
            self.assertEqual(saved["keywords"][0]["phrase"], "تأخیر پرداخت")
            self.assertIsNotNone(saved["keywords"][0]["id"])
            self.assertIsNotNone(saved["keywords"][0]["keyword_id"])
            self.assertEqual(saved["keywords"][0]["source_type"], "message")
            self.assertEqual(saved["keywords"][0]["source_id"], posted["id"])
            self.assertEqual(saved["keywords"][0]["project_id"], project_id)
            self.assertEqual(saved["keywords"][0]["created_by_user_id"], ali.user_id)
            self.assertEqual(saved["topic_count"], 1)
            self.assertEqual(saved["emotion_count"], 1)
            self.assertEqual(len(saved["mentions"]), 2)
            self.assertEqual(saved["mentions"][0]["type"], "PERSON")
            self.assertEqual(saved["mentions"][0]["status"], "candidate")
            self.assertIsNotNone(saved["mentions"][0]["id"])
            self.assertEqual(saved["topics"][0]["code"], "finance.payment.delay")
            self.assertIsNotNone(saved["topics"][0]["topic_id"])
            self.assertTrue(saved["topics"][0]["is_primary"])
            self.assertEqual(saved["topics"][0]["mention_text"], "تأخیر پرداخت")
            self.assertEqual(saved["sentiment"]["polarity"], "negative")
            self.assertEqual(
                saved["sentiment"]["mention_text"], "تأخیر پرداخت پیمانکار"
            )
            self.assertEqual(saved["emotions"][0]["emotion"], "worry")
            self.assertEqual(saved["emotions"][0]["mention_text"], "تأخیر پرداخت")
            self.assertEqual(saved["discourse_count"], 2)
            self.assertEqual(saved["discourses"][0]["code"], "issue")
            self.assertTrue(saved["discourses"][0]["is_primary"])
            self.assertEqual(
                saved["discourses"][0]["mention_text"], "تأخیر پرداخت پیمانکار"
            )
            self.assertEqual(saved["intent_count"], 1)
            self.assertEqual(saved["intents"][0]["code"], "report_problem")
            self.assertEqual(
                saved["intents"][0]["mention_text"],
                "تأخیر پرداخت پیمانکار را گزارش کرد",
            )
            self.assertEqual(
                saved["intents"][0]["slots"]["گزارش‌دهنده"],
                "سارا احمدی",
            )
            self.assertEqual(
                saved["intents"][0]["slots"]["مسئله"],
                "تأخیر پرداخت پیمانکار",
            )
            self.assertEqual(saved["rhetoric_count"], 1)
            self.assertEqual(saved["rhetorics"][0]["code"], "literal")
            self.assertEqual(
                saved["intended_meaning"],
                "تأخیر پرداخت پیمانکار گزارش شد",
            )
            loaded = run_get_text_analysis(id=saved["id"])
            self.assertEqual(loaded["status"], "success")
            self.assertEqual(loaded["id"], saved["id"])
            self.assertEqual(loaded["mention_count"], 2)
            self.assertEqual(loaded["keyword_count"], 1)
            listed = run_list_text_analyses(source_type="message", source_id=posted["id"])
            self.assertEqual(listed["status"], "success")
            self.assertIn(saved["id"], {row["id"] for row in listed["records"]})
            outsider = bind_actor_as_role("مدیر پروژه")
            try:
                hidden = run_get_text_analysis(id=saved["id"])
                self.assertEqual(hidden["status"], "error")
                self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
            finally:
                outsider.close()
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_save_playground_text_as_content(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            saved = run_save_text_analysis(
                source_type="content",
                text="پیمانکار تا پایان هفته قطعه را به کارگاه می‌رساند.",
                mentions=[
                    {
                        "type": "TIME",
                        "canonical_name": "پایان هفته",
                        "normalized_name": f"پایان هفته {uuid.uuid4().hex[:12]}",
                        "mention_text": "پایان هفته",
                        "start_offset": 12,
                        "end_offset": 22,
                        "confidence": 0.7,
                        "occurred_at": "2026-09-19T00:00:00",
                    }
                ],
            )
            self.assertEqual(saved["status"], "success")
            self.assertEqual(saved["source_type"], "content")
            self.assertGreaterEqual(saved["source_id"], 1)
            self.assertIsNone(saved.get("project_id"))
            self.assertEqual(saved["mentions"][0]["occurred_at"][:10], "2026-09-19")
            missing = run_get_text_analysis(id=9_999_999)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], TEXT_ANALYSIS_NOT_FOUND)
            bad_type = run_save_text_analysis(
                source_type="report",
                source_id=1,
                mentions=[{"type": "ACTION", "canonical_name": "x", "mention_text": "x",
                           "start_offset": 0, "end_offset": 1}],
            )
            self.assertEqual(bad_type["status"], "error")
            self.assertEqual(bad_type["error_code"], INVALID_INPUT)
        finally:
            ali.close()

    def test_save_discovered_discourse_creates_type(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        code = f"pledge_{uuid.uuid4().hex[:8]}"
        try:
            saved = run_save_text_analysis(
                source_type="content",
                text="متعهد می‌شوم قطعه را به کارگاه برسانم.",
                discourses=[
                    {
                        "code": code,
                        "name": f"تعهد {code[-4:]}",
                        "discovered": True,
                        "definition": "اعلام پایبندی گوینده به انجام کار",
                        "is_primary": True,
                        "mention_text": "متعهد می‌شوم",
                        "confidence": 0.86,
                        "required_slots": [
                            {"name": "متعهد", "description": "گوینده"},
                            {"name": "عمل تعهدشده", "description": "کار"},
                        ],
                        "slots": {
                            "متعهد": "متعهد می‌شوم",
                            "عمل تعهدشده": "قطعه را به کارگاه برسانم",
                        },
                    }
                ],
            )
            self.assertEqual(saved["status"], "success")
            self.assertEqual(saved["discourses"][0]["code"], code)
            self.assertTrue(saved["discourses"][0].get("is_discovered"))
            self.assertEqual(saved["discourses"][0]["slots"]["متعهد"], "متعهد می‌شوم")
        finally:
            ali.close()

    def test_save_sample_facts_roundtrip_on_analysis(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            saved = run_save_text_analysis(
                source_type="content",
                text=(
                    "دیروز رفتم واحد مالی گفت :\n"
                    "به دلیل کمبود نیروی متخصص ۳۰ درصد کاهش عملکرد داریم که البته "
                    "۱۰ درصد آن مربوط به واحد بازاریابی است نه صرفا نبود نیروی متخصص"
                ),
                facts=[
                    {
                        "id": "q1",
                        "kind": "quantity",
                        "name": "کاهش عملکرد",
                        "value": 30,
                        "unit": "percent",
                        "role": "total",
                        "grounding": "explicit",
                        "mention_text": "۳۰ درصد کاهش عملکرد",
                        "confidence": 0.95,
                    },
                    {
                        "id": "q2",
                        "kind": "quantity",
                        "name": "سهم بازاریابی",
                        "value": 10,
                        "unit": "percent",
                        "role": "part",
                        "grounding": "explicit",
                        "mention_text": "۱۰ درصد آن مربوط به واحد بازاریابی",
                        "confidence": 0.95,
                    },
                    {
                        "id": "q3",
                        "kind": "quantity",
                        "name": "سهم کمبود نیروی متخصص",
                        "value": 20,
                        "unit": "percent",
                        "role": "remainder",
                        "grounding": "derived",
                        "derivation": "subtract",
                        "source_ids": ["q1", "q2"],
                        "mention_text": "کمبود نیروی متخصص",
                        "evidence_texts": [
                            "۳۰ درصد کاهش عملکرد",
                            "۱۰ درصد آن مربوط به واحد بازاریابی",
                        ],
                        "confidence": 0.9,
                    },
                    {
                        "id": "c1",
                        "kind": "cause",
                        "name": "کمبود نیروی متخصص",
                        "effect": "کاهش عملکرد",
                        "grounding": "explicit",
                        "mention_text": "کمبود نیروی متخصص",
                        "confidence": 0.9,
                    },
                    {
                        "id": "c2",
                        "kind": "cause",
                        "name": "واحد بازاریابی",
                        "effect": "کاهش عملکرد",
                        "grounding": "explicit",
                        "mention_text": "واحد بازاریابی",
                        "confidence": 0.85,
                    },
                ],
                quotes=[
                    {
                        "mode": "indirect",
                        "attributed_to": "واحد مالی",
                        "quoted_text": "به دلیل کمبود نیروی متخصص ۳۰ درصد کاهش عملکرد داریم",
                        "mention_text": "گفت",
                        "confidence": 0.9,
                    }
                ],
            )
            self.assertEqual(saved["status"], "success")
            self.assertEqual(saved["fact_count"], 5)
            quantities = [row for row in saved["facts"] if row["kind"] == "quantity"]
            causes = [row for row in saved["facts"] if row["kind"] == "cause"]
            self.assertEqual(len(quantities), 3)
            self.assertEqual(len(causes), 2)
            by_role = {row["role"]: row for row in quantities}
            self.assertEqual(by_role["total"]["value"], 30)
            self.assertEqual(by_role["part"]["value"], 10)
            self.assertEqual(by_role["remainder"]["value"], 20)
            self.assertEqual(by_role["total"]["unit"], "percent")
            self.assertEqual(by_role["remainder"]["grounding"], "derived")
            self.assertEqual(by_role["remainder"]["derivation"], "subtract")
            self.assertEqual(
                {row["name"] for row in causes},
                {"کمبود نیروی متخصص", "واحد بازاریابی"},
            )
            self.assertEqual(saved["quote_count"], 1)
            self.assertEqual(saved["quotes"][0]["attributed_to"], "واحد مالی")
            self.assertEqual(saved["quotes"][0]["mode"], "indirect")
            self.assertIn("کمبود نیروی متخصص", saved["quotes"][0]["quoted_text"])
            loaded = run_get_text_analysis(id=saved["id"])
            self.assertEqual(loaded["status"], "success")
            self.assertEqual(loaded["fact_count"], 5)
            loaded_qty = {
                row["role"]: row["value"]
                for row in loaded["facts"]
                if row["kind"] == "quantity"
            }
            self.assertEqual(loaded_qty, {"total": 30, "part": 10, "remainder": 20})
            self.assertEqual(
                {row["name"] for row in loaded["facts"] if row["kind"] == "cause"},
                {"کمبود نیروی متخصص", "واحد بازاریابی"},
            )
            self.assertEqual(loaded["quote_count"], 1)
            self.assertEqual(loaded["quotes"][0]["attributed_to"], "واحد مالی")
            self.assertEqual(loaded["quotes"][0]["mode"], "indirect")
            listed = run_list_text_analyses(
                source_type="content",
                source_id=saved["source_id"],
            )
            self.assertEqual(listed["status"], "success")
            match = next(row for row in listed["records"] if row["id"] == saved["id"])
            self.assertEqual(match["fact_count"], 5)
            self.assertEqual(match["quote_count"], 1)
            bad_kind = run_save_text_analysis(
                source_type="content",
                text="۳۰ درصد",
                facts=[{"kind": "guess", "name": "حدس", "grounding": "explicit"}],
            )
            self.assertEqual(bad_kind["status"], "error")
            self.assertEqual(bad_kind["error_code"], INVALID_INPUT)
            bad_mode = run_save_text_analysis(
                source_type="content",
                text="واحد مالی گفت کاهش عملکرد داریم",
                quotes=[
                    {
                        "mode": "whisper",
                        "attributed_to": "واحد مالی",
                        "quoted_text": "کاهش عملکرد داریم",
                    }
                ],
            )
            self.assertEqual(bad_mode["status"], "error")
            self.assertEqual(bad_mode["error_code"], INVALID_INPUT)
        finally:
            ali.close()


class IssueToolTests(unittest.TestCase):
    """ثبت کارت مسئله با منبع تحلیل و محدودهٔ فهرست."""

    def test_create_issue_is_registered_as_writable(self) -> None:
        from mcp_server.server import mcp

        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        tool = by_name["create_issue"]
        self.assertEqual(tool.title, TITLE_CREATE_ISSUE)
        self.assertFalse(tool.annotations.read_only_hint)
        required = set(tool.input_schema.get("required") or [])
        self.assertIn("project_id", required)
        self.assertIn("title", required)
        self.assertIn("analysis_id", required)
        self.assertNotIn("created_by_user_id", tool.input_schema.get("properties") or {})
        get_tool = by_name["get_issue"]
        self.assertEqual(get_tool.title, TITLE_GET_ISSUE)
        self.assertTrue(get_tool.annotations.read_only_hint)
        list_tool = by_name["list_issues"]
        self.assertEqual(list_tool.title, TITLE_LIST_ISSUES)
        self.assertTrue(list_tool.annotations.read_only_hint)
        link_tool = by_name["link_issue_cause"]
        self.assertEqual(link_tool.title, TITLE_LINK_ISSUE_CAUSE)
        self.assertFalse(link_tool.annotations.read_only_hint)
        link_required = set(link_tool.input_schema.get("required") or [])
        self.assertIn("issue_id", link_required)
        self.assertIn("cause_issue_id", link_required)
        self.assertNotIn("task_id", link_tool.input_schema.get("properties") or {})
        task_link = by_name["link_issue_task"]
        self.assertEqual(task_link.title, TITLE_LINK_ISSUE_TASK)
        self.assertFalse(task_link.annotations.read_only_hint)
        task_required = set(task_link.input_schema.get("required") or [])
        self.assertIn("issue_id", task_required)
        self.assertIn("task_id", task_required)
        self.assertNotIn("title", task_link.input_schema.get("properties") or {})
        importance_tool = by_name["set_issue_importance"]
        self.assertEqual(importance_tool.title, TITLE_SET_ISSUE_IMPORTANCE)
        self.assertFalse(importance_tool.annotations.read_only_hint)
        self.assertIn("issue_id", set(importance_tool.input_schema.get("required") or []))
        urgency_tool = by_name["set_issue_urgency"]
        self.assertEqual(urgency_tool.title, TITLE_SET_ISSUE_URGENCY)
        self.assertFalse(urgency_tool.annotations.read_only_hint)
        severity_tool = by_name["set_issue_severity"]
        self.assertEqual(severity_tool.title, TITLE_SET_ISSUE_SEVERITY)
        self.assertFalse(severity_tool.annotations.read_only_hint)
        impact_tool = by_name["add_issue_impact"]
        self.assertEqual(impact_tool.title, TITLE_ADD_ISSUE_IMPACT)
        self.assertFalse(impact_tool.annotations.read_only_hint)
        impact_required = set(impact_tool.input_schema.get("required") or [])
        self.assertIn("issue_id", impact_required)
        self.assertNotIn("description", impact_required)
        topic_tool = by_name["link_issue_topic"]
        self.assertEqual(topic_tool.title, TITLE_LINK_ISSUE_TOPIC)
        self.assertFalse(topic_tool.annotations.read_only_hint)
        topic_required = set(topic_tool.input_schema.get("required") or [])
        self.assertIn("issue_id", topic_required)
        entity_tool = by_name["link_issue_entity"]
        self.assertEqual(entity_tool.title, TITLE_LINK_ISSUE_ENTITY)
        self.assertFalse(entity_tool.annotations.read_only_hint)
        entity_required = set(entity_tool.input_schema.get("required") or [])
        self.assertIn("issue_id", entity_required)
        self.assertIn("entity_id", entity_required)

    def test_save_analysis_then_create_issue_with_source(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        issue_id = None
        try:
            created = run_create_project(
                name=unique_project_name("مسئله"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            analysis_id = _insert_content_analysis(
                ali.user_id,
                "واحد مالی به‌خاطر کمبود نیروی متخصص ۳۰ درصد کاهش عملکرد داشته است.",
            )
            saved = run_create_issue(
                project_id=project_id,
                title=unique_issue_title("کاهش عملکرد واحد مالی"),
                analysis_id=analysis_id,
            )
            self.assertEqual(saved["status"], "success")
            issue_id = saved["id"]
            self.assertEqual(saved["status_name"], "جدید")
            self.assertEqual(saved["status_code"], "new")
            self.assertEqual(saved["project_id"], project_id)
            self.assertIn(analysis_id, saved["analysis_ids"])
            self.assertEqual(saved["sources"][0]["analysis_id"], analysis_id)
            self.assertEqual(saved["causes"], [])
            self.assertEqual(saved["tasks"], [])
            self.assertIsNone(saved["importance"])
            self.assertIsNone(saved["urgency"])
            self.assertIsNone(saved["severity"])
            self.assertEqual(saved["impacts"], [])
            self.assertEqual(saved["topics"], [])
            self.assertEqual(saved["entities"], [])
            self.assertFalse(saved["reused"])
            loaded = run_get_issue(id=issue_id)
            self.assertEqual(loaded["status"], "success")
            self.assertEqual(loaded["id"], issue_id)
            self.assertEqual(loaded["analysis_ids"], [analysis_id])
            listed = run_list_issues(project_id=project_id, limit=50)
            self.assertEqual(listed["status"], "success")
            self.assertIn(issue_id, {row["id"] for row in listed["records"]})
            reused = run_create_issue(
                project_id=project_id,
                title=unique_issue_title("همان منبع"),
                analysis_id=analysis_id,
                status="new",
            )
            self.assertEqual(reused["status"], "success")
            self.assertEqual(reused["status_code"], "new")
            self.assertEqual(reused["analysis_ids"], [analysis_id])
            missing = run_get_issue(id=9_999_999)
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], ISSUE_NOT_FOUND)
            bad_analysis = run_create_issue(
                project_id=project_id,
                title=unique_issue_title("بدون تحلیل"),
                analysis_id=9_999_999,
            )
            self.assertEqual(bad_analysis["status"], "error")
            self.assertEqual(bad_analysis["error_code"], TEXT_ANALYSIS_NOT_FOUND)
            outsider = bind_actor_as_role("مدیر پروژه")
            try:
                hidden = run_get_issue(id=issue_id)
                self.assertEqual(hidden["status"], "error")
                self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
                hidden_list = run_list_issues(project_id=project_id, limit=50)
                self.assertEqual(hidden_list["status"], "error")
                self.assertEqual(hidden_list["error_code"], PERMISSION_DENIED)
            finally:
                outsider.close()
        finally:
            if issue_id is not None:
                delete_temp_issue(issue_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()


    def test_sample_causes_become_linked_issues(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        issue_ids = []
        try:
            created = run_create_project(
                name=unique_project_name("علت"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            analysis_id = _insert_content_analysis(
                ali.user_id,
                "به دلیل کمبود نیروی متخصص ۳۰ درصد کاهش عملکرد داریم "
                "که ۱۰ درصد آن مربوط به واحد بازاریابی است.",
            )
            main = run_create_issue(
                project_id=project_id,
                title="کاهش عملکرد واحد مالی",
                analysis_id=analysis_id,
            )
            staff = run_create_issue(
                project_id=project_id,
                title="کمبود نیروی متخصص",
                analysis_id=analysis_id,
            )
            marketing = run_create_issue(
                project_id=project_id,
                title="واحد بازاریابی",
                analysis_id=analysis_id,
            )
            issue_ids = [main["id"], staff["id"], marketing["id"]]
            self.assertEqual(main["causes"], [])
            linked_staff = run_link_issue_cause(
                issue_id=main["id"],
                cause_issue_id=staff["id"],
                cause_level="cause",
            )
            self.assertEqual(linked_staff["status"], "success")
            self.assertEqual(linked_staff["cause_issue_id"], staff["id"])
            self.assertEqual(linked_staff["cause_title"], "کمبود نیروی متخصص")
            self.assertEqual(linked_staff["cause_level_code"], "cause")
            linked_marketing = run_link_issue_cause(
                issue_id=main["id"],
                cause_issue_id=marketing["id"],
            )
            self.assertEqual(linked_marketing["status"], "success")
            self.assertEqual(linked_marketing["cause_title"], "واحد بازاریابی")
            self.assertEqual(linked_marketing["cause_level_code"], "cause")
            loaded = run_get_issue(id=main["id"])
            self.assertEqual(loaded["status"], "success")
            cause_titles = {row["cause_title"] for row in loaded["causes"]}
            self.assertEqual(cause_titles, {"کمبود نیروی متخصص", "واحد بازاریابی"})
            self.assertTrue(
                all(row["cause_level_code"] == "cause" for row in loaded["causes"])
            )
            self_link = run_link_issue_cause(
                issue_id=main["id"],
                cause_issue_id=main["id"],
            )
            self.assertEqual(self_link["status"], "error")
            self.assertEqual(self_link["error_code"], INVALID_INPUT)
            duplicate = run_link_issue_cause(
                issue_id=main["id"],
                cause_issue_id=staff["id"],
            )
            self.assertEqual(duplicate["status"], "error")
            self.assertEqual(duplicate["error_code"], INVALID_INPUT)
            other = run_create_project(
                name=unique_project_name("پروژه دیگر"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            other_issue = run_create_issue(
                project_id=other["id"],
                title="مسئله پروژه دیگر",
                analysis_id=analysis_id,
            )
            issue_ids.append(other_issue["id"])
            crossed = run_link_issue_cause(
                issue_id=main["id"],
                cause_issue_id=other_issue["id"],
            )
            self.assertEqual(crossed["status"], "error")
            self.assertEqual(crossed["error_code"], INVALID_INPUT)
            outsider = bind_actor_as_role("مدیر پروژه")
            try:
                hidden = run_link_issue_cause(
                    issue_id=main["id"],
                    cause_issue_id=staff["id"],
                    cause_level="root_cause",
                )
                self.assertEqual(hidden["status"], "error")
                self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
            finally:
                outsider.close()
            delete_temp_project(other["id"])
        finally:
            for issue_id in reversed(issue_ids):
                delete_temp_issue(issue_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_sample_task_is_created_and_linked_to_issue(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        issue_id = None
        task_id = None
        try:
            created = run_create_project(
                name=unique_project_name("وظیفه مسئله"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            analysis_id = _insert_content_analysis(
                ali.user_id,
                "به دلیل کمبود نیروی متخصص ۳۰ درصد کاهش عملکرد داریم "
                "که ۱۰ درصد آن مربوط به واحد بازاریابی است.",
            )
            main = run_create_issue(
                project_id=project_id,
                title="کاهش عملکرد واحد مالی",
                analysis_id=analysis_id,
            )
            issue_id = main["id"]
            created_task = run_create_task(
                project_id=project_id,
                title="تأمین نیروی متخصص واحد مالی",
                status="شروع نشده",
                priority="کم",
                importance="کم",
            )
            self.assertEqual(created_task["status"], "success")
            task_id = created_task["id"]
            linked = run_link_issue_task(issue_id=issue_id, task_id=task_id)
            self.assertEqual(linked["status"], "success")
            self.assertEqual(linked["issue_id"], issue_id)
            self.assertEqual(linked["task_id"], task_id)
            self.assertEqual(linked["task_title"], "تأمین نیروی متخصص واحد مالی")
            self.assertIn(analysis_id, linked["analysis_ids"])
            loaded = run_get_issue(id=issue_id)
            self.assertEqual(loaded["status"], "success")
            self.assertEqual(len(loaded["tasks"]), 1)
            self.assertEqual(loaded["tasks"][0]["task_id"], task_id)
            self.assertEqual(
                loaded["tasks"][0]["task_title"],
                "تأمین نیروی متخصص واحد مالی",
            )
            output_type = fetch_first("analysis_output_types", {"code": "task"})
            self.assertIsNotNone(output_type)
            traced = fetch_first(
                "analysis_outputs",
                {
                    "analysis_id": analysis_id,
                    "output_type_id": output_type["id"],
                    "record_id": task_id,
                },
            )
            self.assertIsNotNone(traced)
            duplicate = run_link_issue_task(issue_id=issue_id, task_id=task_id)
            self.assertEqual(duplicate["status"], "error")
            self.assertEqual(duplicate["error_code"], INVALID_INPUT)
            missing_task = run_link_issue_task(issue_id=issue_id, task_id=9_999_999)
            self.assertEqual(missing_task["status"], "error")
            self.assertEqual(missing_task["error_code"], TASK_NOT_FOUND)
            other = run_create_project(
                name=unique_project_name("پروژه وظیفه دیگر"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            other_task = run_create_task(
                project_id=other["id"],
                title="وظیفه پروژه دیگر",
                status="شروع نشده",
                priority="کم",
                importance="کم",
            )
            crossed = run_link_issue_task(
                issue_id=issue_id,
                task_id=other_task["id"],
            )
            self.assertEqual(crossed["status"], "error")
            self.assertEqual(crossed["error_code"], INVALID_INPUT)
            outsider = bind_actor_as_role("مدیر پروژه")
            try:
                hidden = run_link_issue_task(issue_id=issue_id, task_id=task_id)
                self.assertEqual(hidden["status"], "error")
                self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
            finally:
                outsider.close()
            delete_temp_task(other_task["id"])
            delete_temp_project(other["id"])
        finally:
            if issue_id is not None:
                delete_temp_issue(issue_id)
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_sample_issue_gets_catalog_importance_urgency_severity_and_impacts(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        issue_id = None
        task_id = None
        try:
            created = run_create_project(
                name=unique_project_name("امتیاز مسئله"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            analysis_id = _insert_content_analysis(
                ali.user_id,
                "به دلیل کمبود نیروی متخصص ۳۰ درصد کاهش عملکرد داریم "
                "که ۱۰ درصد آن مربوط به واحد بازاریابی است.",
            )
            main = run_create_issue(
                project_id=project_id,
                title="کاهش عملکرد واحد مالی",
                analysis_id=analysis_id,
            )
            issue_id = main["id"]
            created_task = run_create_task(
                project_id=project_id,
                title="تأمین نیروی متخصص واحد مالی",
                status="شروع نشده",
                priority="کم",
                importance="کم",
            )
            task_id = created_task["id"]
            linked = run_link_issue_task(issue_id=issue_id, task_id=task_id)
            self.assertEqual(linked["status"], "success")
            loaded_task = run_get_task(id=task_id)
            self.assertEqual(loaded_task["priority_name"], "کم")
            importance = run_set_issue_importance(
                issue_id=issue_id,
                importance="زیاد",
            )
            self.assertEqual(importance["status"], "success")
            self.assertEqual(importance["importance_name"], "زیاد")
            self.assertIn(analysis_id, importance["analysis_ids"])
            urgency = run_set_issue_urgency(
                issue_id=issue_id,
                priority=loaded_task["priority_name"],
            )
            self.assertEqual(urgency["status"], "success")
            self.assertEqual(urgency["priority_name"], "کم")
            self.assertIn(analysis_id, urgency["analysis_ids"])
            severity = run_set_issue_severity(
                issue_id=issue_id,
                severity="متوسط",
            )
            self.assertEqual(severity["status"], "success")
            self.assertEqual(severity["severity_name"], "متوسط")
            self.assertEqual(severity["severity_code"], "medium")
            hr = run_add_issue_impact(
                issue_id=issue_id,
                impact_type="منابع انسانی",
            )
            self.assertEqual(hr["status"], "success")
            self.assertEqual(hr["impact_type_name"], "منابع انسانی")
            self.assertEqual(hr["impact_type_code"], "hr")
            quality = run_add_issue_impact(
                issue_id=issue_id,
                impact_type="کیفیت",
            )
            self.assertEqual(quality["status"], "success")
            self.assertEqual(quality["impact_type_name"], "کیفیت")
            loaded = run_get_issue(id=issue_id)
            self.assertEqual(loaded["status"], "success")
            self.assertEqual(loaded["importance"]["importance_name"], "زیاد")
            self.assertEqual(loaded["urgency"]["priority_name"], "کم")
            self.assertEqual(loaded["severity"]["severity_name"], "متوسط")
            impact_names = {row["impact_type_name"] for row in loaded["impacts"]}
            self.assertEqual(impact_names, {"منابع انسانی", "کیفیت"})
            analysis_importance = fetch_first(
                "text_analysis_importances",
                {"analysis_id": analysis_id},
            )
            self.assertIsNotNone(analysis_importance)
            task_importance = fetch_first(
                "task_importances",
                {"id": analysis_importance["importance_id"]},
            )
            self.assertEqual(task_importance["name"], "زیاد")
            analysis_urgency = fetch_first(
                "text_analysis_urgencies",
                {"analysis_id": analysis_id},
            )
            self.assertIsNotNone(analysis_urgency)
            task_priority = fetch_first(
                "task_priorities",
                {"id": analysis_urgency["priority_id"]},
            )
            self.assertEqual(task_priority["name"], "کم")
            again = run_set_issue_importance(issue_id=issue_id, importance="زیاد")
            self.assertEqual(again["status"], "success")
            missing = run_set_issue_severity(issue_id=9_999_999, severity="medium")
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], ISSUE_NOT_FOUND)
            bad = run_add_issue_impact(issue_id=issue_id, impact_type="ناموجود")
            self.assertEqual(bad["status"], "error")
            self.assertEqual(bad["error_code"], INVALID_INPUT)
            outsider = bind_actor_as_role("مدیر پروژه")
            try:
                hidden = run_set_issue_importance(
                    issue_id=issue_id,
                    importance="زیاد",
                )
                self.assertEqual(hidden["status"], "error")
                self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
            finally:
                outsider.close()
        finally:
            if issue_id is not None:
                delete_temp_issue(issue_id)
            if task_id is not None:
                delete_temp_task(task_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()


    def test_saved_ner_topics_and_entities_link_to_canonical_issue(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        issue_id = None
        try:
            created = run_create_project(
                name=unique_project_name("موضوع مسئله"),
                project_type="نرم‌افزاری",
                project_status="در حال اجرا",
            )
            project_id = created["id"]
            suffix = str(project_id)
            first_text = "واحد مالی ۳۰ درصد کاهش عملکرد داشته است."
            analysis_id, entity_id, topic_id = _insert_ner_content_analysis(
                ali.user_id,
                first_text,
                unit_name=f"واحد مالی {suffix}",
                topic_code="finance.payment.delay",
            )
            main = run_create_issue(
                project_id=project_id,
                title="کاهش عملکرد مالی",
                analysis_id=analysis_id,
            )
            self.assertEqual(main["status"], "success")
            issue_id = main["id"]
            self.assertFalse(main["reused"])
            self.assertEqual(main["topics"], [])
            self.assertEqual(main["entities"], [])
            linked_topic = run_link_issue_topic(
                issue_id=issue_id,
                topic="finance.payment.delay",
            )
            self.assertEqual(linked_topic["status"], "success")
            self.assertEqual(linked_topic["topic_id"], topic_id)
            self.assertEqual(linked_topic["topic_code"], "finance.payment.delay")
            linked_entity = run_link_issue_entity(
                issue_id=issue_id,
                entity_id=entity_id,
                role="affected",
            )
            self.assertEqual(linked_entity["status"], "success")
            self.assertEqual(linked_entity["canonical_name"], "واحد مالی")
            self.assertEqual(linked_entity["entity_type"], "UNIT")
            self.assertEqual(linked_entity["role_code"], "affected")
            self.assertEqual(linked_entity["role_name"], "متأثر")
            loaded = run_get_issue(id=issue_id)
            self.assertEqual(loaded["status"], "success")
            self.assertEqual(
                {row["topic_code"] for row in loaded["topics"]},
                {"finance.payment.delay"},
            )
            self.assertEqual(loaded["entities"][0]["canonical_name"], "واحد مالی")
            self.assertEqual(loaded["entities"][0]["role_code"], "affected")
            second_text = "گزارش دوم: واحد مالی هنوز کاهش عملکرد دارد."
            start = second_text.index("واحد مالی")
            second_id, second_entity_id, _ = _insert_ner_content_analysis(
                ali.user_id,
                second_text,
                unit_name=f"واحد مالی {suffix}",
                topic_code="finance.payment.delay",
                start_offset=start,
            )
            self.assertEqual(second_entity_id, entity_id)
            reused = run_create_issue(
                project_id=project_id,
                title="کاهش عملکرد مالی",
                analysis_id=second_id,
            )
            self.assertEqual(reused["status"], "success")
            self.assertTrue(reused["reused"])
            self.assertEqual(reused["id"], issue_id)
            self.assertEqual(
                set(reused["analysis_ids"]),
                {analysis_id, second_id},
            )
            self.assertEqual(len(reused["sources"]), 2)
            self.assertEqual(reused["entities"][0]["canonical_name"], "واحد مالی")
            duplicate_topic = run_link_issue_topic(
                issue_id=issue_id,
                topic_id=topic_id,
            )
            self.assertEqual(duplicate_topic["status"], "error")
            self.assertEqual(duplicate_topic["error_code"], INVALID_INPUT)
            duplicate_entity = run_link_issue_entity(
                issue_id=issue_id,
                entity_id=entity_id,
                role="affected",
            )
            self.assertEqual(duplicate_entity["status"], "error")
            self.assertEqual(duplicate_entity["error_code"], INVALID_INPUT)
            other_topic = run_link_issue_topic(
                issue_id=issue_id,
                topic="tech.software",
            )
            self.assertEqual(other_topic["status"], "error")
            self.assertEqual(other_topic["error_code"], INVALID_INPUT)
            outsider = bind_actor_as_role("مدیر پروژه")
            try:
                hidden = run_link_issue_topic(
                    issue_id=issue_id,
                    topic_id=topic_id,
                )
                self.assertEqual(hidden["status"], "error")
                self.assertEqual(hidden["error_code"], PERMISSION_DENIED)
            finally:
                outsider.close()
        finally:
            if issue_id is not None:
                delete_temp_issue(issue_id)
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()


def _insert_content_analysis(user_id: int, text: str) -> int:
    """یک تحلیل content بدون بار کردن ذکرها درج می‌کند."""
    source_type = fetch_first("analysis_source_types", {"code": "content"})
    text_kind = fetch_first("content_kinds", {"code": "TEXT"})
    if source_type is None or text_kind is None:
        raise AssertionError("lookup نوع منبع content یا نوع TEXT نیست")

    def work(connection):
        content_id = insert_row_on(
            connection,
            "contents",
            {
                "content_kind_id": text_kind["id"],
                "text_body": text,
                "created_by_user_id": user_id,
            },
        )
        return insert_row_on(
            connection,
            "text_analyses",
            {
                "source_type_id": source_type["id"],
                "source_id": content_id,
                "model": "test-issue",
                "created_by_user_id": user_id,
            },
        )

    return run_query(work)


def _insert_ner_content_analysis(
    user_id: int,
    text: str,
    unit_name: str,
    topic_code: str,
    start_offset: int = 0,
) -> tuple:
    """تحلیل content با موضوع و موجودیت ذخیره‌شدهٔ NER درج می‌کند."""
    analysis_id = _insert_content_analysis(user_id, text)
    entity_type = fetch_first("entity_types", {"code": "UNIT"})
    status = fetch_first("entity_statuses", {"code": "candidate"})
    topic = fetch_first("topics", {"code": topic_code})
    if entity_type is None or status is None or topic is None:
        raise AssertionError("lookup نوع واحد، وضعیت موجودیت یا موضوع نیست")
    end_offset = start_offset + len("واحد مالی")

    def work(connection):
        existing = fetch_first(
            "entities",
            {
                "entity_type_id": entity_type["id"],
                "normalized_name": unit_name,
            },
        )
        if existing is None:
            entity_id = insert_row_on(
                connection,
                "entities",
                {
                    "entity_type_id": entity_type["id"],
                    "status_id": status["id"],
                    "canonical_name": "واحد مالی",
                    "normalized_name": unit_name,
                },
            )
        else:
            entity_id = existing["id"]
        insert_row_on(
            connection,
            "entity_mentions",
            {
                "analysis_id": analysis_id,
                "entity_id": entity_id,
                "mention_text": "واحد مالی",
                "start_offset": start_offset,
                "end_offset": end_offset,
                "confidence": 0.9,
            },
        )
        insert_row_on(
            connection,
            "text_analysis_topics",
            {
                "analysis_id": analysis_id,
                "topic_id": topic["id"],
                "is_primary": True,
                "confidence": 0.8,
                "mention_text": "کاهش عملکرد",
            },
        )
        return entity_id, topic["id"]

    entity_id, topic_id = run_query(work)
    return analysis_id, entity_id, topic_id


def _count_user_transactions(user_id: int) -> int:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM financial_transactions WHERE user_id = %s",
                [user_id],
            )
            return int(cursor.fetchone()[0])
    finally:
        connection.close()


def _fetch_transaction(transaction_id: int) -> dict:
    connection = open_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT tx.id, tx.account_id, tx.amount, tt.name
                FROM financial_transactions tx
                JOIN transaction_types tt ON tt.id = tx.transaction_type_id
                WHERE tx.id = %s
                """,
                [transaction_id],
            )
            row = cursor.fetchone()
    finally:
        connection.close()
    if row is None:
        raise AssertionError("تراکنش نقدی ساخته نشد")
    return {
        "id": row[0],
        "account_id": row[1],
        "amount": row[2],
        "name": row[3],
    }


if __name__ == "__main__":
    unittest.main()
