package ir.management.organization;

import android.Manifest;
import android.content.ContentUris;
import android.database.Cursor;
import android.net.Uri;
import android.provider.CalendarContract;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

/**
 * رویدادهای تقویم گوشی را می‌خواند؛ اگر حساب گوگل سینک باشد همان Google Calendar است.
 */
@CapacitorPlugin(
    name = "DeviceCalendar",
    permissions = {
        @Permission(alias = "calendar", strings = { Manifest.permission.READ_CALENDAR })
    }
)
public class DeviceCalendarPlugin extends Plugin {

    private static final String[] PROJECTION = {
        CalendarContract.Instances.EVENT_ID,
        CalendarContract.Instances.TITLE,
        CalendarContract.Instances.BEGIN,
        CalendarContract.Instances.END,
        CalendarContract.Instances.EVENT_LOCATION,
        CalendarContract.Instances.ALL_DAY,
        CalendarContract.Instances.CALENDAR_DISPLAY_NAME,
        CalendarContract.Calendars.ACCOUNT_TYPE,
        CalendarContract.Instances.DESCRIPTION
    };

    @PluginMethod
    public void listEvents(PluginCall call) {
        if (getPermissionState("calendar") != PermissionState.GRANTED) {
            requestPermissionForAlias("calendar", call, "onCalendarPermission");
            return;
        }
        readEvents(call);
    }

    @PermissionCallback
    private void onCalendarPermission(PluginCall call) {
        if (getPermissionState("calendar") == PermissionState.GRANTED) {
            readEvents(call);
            return;
        }
        call.reject("برای خواندن تقویم گوگل باید مجوز تقویم را بدهید");
    }

    private void readEvents(PluginCall call) {
        long now = System.currentTimeMillis();
        long fromMs = call.getLong("fromMs", now - 12L * 60L * 60L * 1000L);
        long toMs = call.getLong("toMs", now + 60L * 24L * 60L * 60L * 1000L);
        boolean googleOnly = Boolean.TRUE.equals(call.getBoolean("googleOnly", true));
        try {
            LoadResult first = queryEvents(fromMs, toMs, googleOnly);
            LoadResult used = first;
            if (googleOnly && first.events.length() == 0) {
                used = queryEvents(fromMs, toMs, false);
            }
            JSObject payload = new JSObject();
            payload.put("events", used.events);
            payload.put("googleCalendars", used.googleOnlyQuery && first.events.length() > 0);
            payload.put("usedGoogleFilter", googleOnly && first.events.length() > 0);
            call.resolve(payload);
        } catch (Exception error) {
            call.reject(error.getMessage() == null ? "خواندن تقویم ممکن نشد" : error.getMessage());
        }
    }

    private LoadResult queryEvents(long fromMs, long toMs, boolean googleOnly) {
        Uri.Builder builder = CalendarContract.Instances.CONTENT_URI.buildUpon();
        ContentUris.appendId(builder, fromMs);
        ContentUris.appendId(builder, toMs);
        String selection = googleOnly ? CalendarContract.Calendars.ACCOUNT_TYPE + " = ?" : null;
        String[] args = googleOnly ? new String[] { "com.google" } : null;
        JSArray events = new JSArray();
        Cursor cursor = getContext()
            .getContentResolver()
            .query(builder.build(), PROJECTION, selection, args, CalendarContract.Instances.BEGIN + " ASC");
        if (cursor == null) {
            return new LoadResult(events, googleOnly);
        }
        try {
            int idIdx = cursor.getColumnIndexOrThrow(CalendarContract.Instances.EVENT_ID);
            int titleIdx = cursor.getColumnIndexOrThrow(CalendarContract.Instances.TITLE);
            int beginIdx = cursor.getColumnIndexOrThrow(CalendarContract.Instances.BEGIN);
            int endIdx = cursor.getColumnIndexOrThrow(CalendarContract.Instances.END);
            int locIdx = cursor.getColumnIndexOrThrow(CalendarContract.Instances.EVENT_LOCATION);
            int allDayIdx = cursor.getColumnIndexOrThrow(CalendarContract.Instances.ALL_DAY);
            int calIdx = cursor.getColumnIndexOrThrow(CalendarContract.Instances.CALENDAR_DISPLAY_NAME);
            int typeIdx = cursor.getColumnIndex(CalendarContract.Calendars.ACCOUNT_TYPE);
            int descIdx = cursor.getColumnIndexOrThrow(CalendarContract.Instances.DESCRIPTION);
            int count = 0;
            while (cursor.moveToNext() && count < 120) {
                long begin = cursor.getLong(beginIdx);
                long end = cursor.getLong(endIdx);
                if (end <= fromMs) {
                    continue;
                }
                JSObject item = new JSObject();
                long eventId = cursor.getLong(idIdx);
                item.put("id", eventId + ":" + begin);
                item.put("eventId", eventId);
                item.put("title", nullable(cursor.getString(titleIdx)));
                item.put("startMs", begin);
                item.put("endMs", end);
                item.put("location", nullable(cursor.getString(locIdx)));
                item.put("allDay", cursor.getInt(allDayIdx) == 1);
                item.put("calendarName", nullable(cursor.getString(calIdx)));
                item.put("accountType", typeIdx >= 0 ? nullable(cursor.getString(typeIdx)) : "");
                item.put("description", nullable(cursor.getString(descIdx)));
                events.put(item);
                count += 1;
            }
        } finally {
            cursor.close();
        }
        return new LoadResult(events, googleOnly);
    }

    private static String nullable(String value) {
        return value == null ? "" : value;
    }

    private static final class LoadResult {
        final JSArray events;
        final boolean googleOnlyQuery;

        LoadResult(JSArray events, boolean googleOnlyQuery) {
            this.events = events;
            this.googleOnlyQuery = googleOnlyQuery;
        }
    }
}
