package tech.nullai.zothcursorz;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.os.Build;
import android.view.accessibility.AccessibilityEvent;

public class ComputerUseAccessibilityService extends AccessibilityService {
    private static ComputerUseAccessibilityService instance;

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
    }

    public static ComputerUseAccessibilityService getInstance() {
        return instance;
    }

    public boolean dispatchTap(float x, float y) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false;

        Path path = new Path();
        path.moveTo(x, y);

        GestureDescription.Builder builder = new GestureDescription.Builder();
        GestureDescription.StrokeDescription stroke = new GestureDescription.StrokeDescription(path, 0, 50);
        builder.addStroke(stroke);

        return dispatchGesture(builder.build(), null, null);
    }

    public boolean dispatchSwipe(float x1, float y1, float x2, float y2, int durationMs) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false;

        Path path = new Path();
        path.moveTo(x1, y1);
        path.lineTo(x2, y2);

        GestureDescription.Builder builder = new GestureDescription.Builder();
        GestureDescription.StrokeDescription stroke = new GestureDescription.StrokeDescription(path, 0, durationMs);
        builder.addStroke(stroke);

        return dispatchGesture(builder.build(), null, null);
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // Monitored for window transitions and automated pre-flight layout validation
    }

    @Override
    public void onInterrupt() {
        instance = null;
    }
}
