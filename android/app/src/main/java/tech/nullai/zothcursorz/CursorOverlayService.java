package tech.nullai.zothcursorz;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;

public class CursorOverlayService extends Service {
    private static final String CHANNEL_ID = "zoth_cursorz_channel";
    private WindowManager windowManager;
    private MultiCursorView overlayView;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        startForeground(1001, buildNotification());

        windowManager = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
        overlayView = new MultiCursorView(this);

        int layoutType;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            layoutType = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            layoutType = WindowManager.LayoutParams.TYPE_PHONE;
        }

        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                layoutType,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN |
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT
        );

        params.gravity = Gravity.TOP | Gravity.START;
        try {
            windowManager.addView(overlayView, params);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "Zoth Cursorz Service",
                    NotificationManager.IMPORTANCE_LOW
            );
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    private Notification buildNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            return new Notification.Builder(this, CHANNEL_ID)
                    .setContentTitle("Zoth Cursorz Active")
                    .setContentText("Multi-agent virtual cursors rendering on screen")
                    .setSmallIcon(R.drawable.ic_launcher)
                    .build();
        }
        return new Notification();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (overlayView != null && windowManager != null) {
            windowManager.removeView(overlayView);
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    // Custom Canvas View for rendering virtual cursors, Braille glyphs, and ripples
    private class MultiCursorView extends View {
        private Paint paint;
        private Paint textPaint;
        private float cur1X = 300, cur1Y = 600;
        private float cur2X = 550, cur2Y = 800;

        public MultiCursorView(Context context) {
            super(context);
            paint = new Paint(Paint.ANTI_ALIAS_FLAG);
            textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            textPaint.setColor(Color.WHITE);
            textPaint.setTextSize(28f);
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);

            // 1. Agent 1nc0gn30 (Neon Green)
            paint.setColor(Color.parseColor("#39d353"));
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(5f);
            canvas.drawCircle(cur1X, cur1Y, 32f, paint);
            canvas.drawLine(cur1X - 45, cur1Y, cur1X + 45, cur1Y, paint);
            canvas.drawLine(cur1X, cur1Y - 45, cur1X, cur1Y + 45, paint);

            paint.setStyle(Paint.Style.FILL);
            paint.setColor(Color.parseColor("#151c2e"));
            canvas.drawRect(cur1X + 40, cur1Y - 20, cur1X + 220, cur1Y + 20, paint);
            canvas.drawText("⣿ 1nc0gn30", cur1X + 50, cur1Y + 8, textPaint);

            // 2. Agent Zoth (24K Gold)
            paint.setColor(Color.parseColor("#f5b82e"));
            paint.setStyle(Paint.Style.STROKE);
            canvas.drawCircle(cur2X, cur2Y, 26f, paint);
            canvas.drawLine(cur2X - 35, cur2Y, cur2X + 35, cur2Y, paint);

            paint.setStyle(Paint.Style.FILL);
            paint.setColor(Color.parseColor("#151c2e"));
            canvas.drawRect(cur2X + 35, cur2Y - 18, cur2X + 180, cur2Y + 18, paint);
            canvas.drawText("⬡ Zoth", cur2X + 45, cur2Y + 8, textPaint);
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            // Forward pass-through or allow dragging agent 1nc0gn30
            if (event.getAction() == MotionEvent.ACTION_MOVE) {
                float dx = event.getX() - cur1X;
                float dy = event.getY() - cur1Y;
                if (Math.hypot(dx, dy) < 120) {
                    cur1X = event.getX();
                    cur1Y = event.getY();
                    invalidate();
                    return true;
                }
            }
            return false;
        }
    }
}
