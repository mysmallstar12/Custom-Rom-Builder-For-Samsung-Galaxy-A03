#!/usr/bin/env python3
"""Apply the A03 LiteOS Android 13 source changes.

The script intentionally uses exact, one-shot replacements.  If LineageOS or
MindTheGapps changes one of the touched files, the build stops instead of
silently producing a ROM without one of the promised features.
"""

from pathlib import Path
import sys


ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def replace_once(relative_path: str, old: str, new: str) -> None:
    path = ROOT / relative_path
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"expected exactly one match in {relative_path}, got {count}: {old[:100]!r}"
        )
    path.write_text(text.replace(old, new, 1))


def write(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ---------------------------------------------------------------------------
# SystemUI: put a real media-volume slider beside the brightness slider.
# This is compiled into SystemUI and does not rely on an overlay or helper app.
# ---------------------------------------------------------------------------
layout = "packages/SystemUI/res/layout/quick_settings_brightness_dialog.xml"
replace_once(
    layout,
    """        <ImageView
            android:id="@+id/brightness_icon"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_gravity="center_vertical"
            android:layout_marginStart="4dp"
            android:layout_marginEnd="8dp"
            android:src="@drawable/ic_qs_brightness_auto_off"
            android:contentDescription="@null"
            android:visibility="gone"
        />
""",
    """        <ImageView
            android:id="@+id/brightness_icon"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_gravity="center_vertical"
            android:layout_marginStart="4dp"
            android:src="@drawable/ic_qs_brightness_auto_off"
            android:contentDescription="@null"
            android:visibility="gone"
        />

        <ImageView
            android:id="@+id/a03_volume_icon"
            android:layout_width="24dp"
            android:layout_height="24dp"
            android:layout_gravity="center_vertical"
            android:layout_marginStart="8dp"
            android:layout_marginEnd="6dp"
            android:contentDescription="@string/accessibility_volume_settings"
            android:src="@drawable/ic_a03_volume"
            android:tint="?android:attr/textColorPrimary"
        />

        <com.android.systemui.settings.brightness.ToggleSeekBar
            android:id="@+id/a03_volume_slider"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_gravity="center_vertical"
            android:layout_weight="1"
            android:minHeight="48dp"
            android:thumb="@null"
            android:background="@null"
            android:paddingStart="0dp"
            android:paddingEnd="0dp"
            android:progressDrawable="@drawable/brightness_progress_drawable"
            android:splitTrack="false"
        />
""",
)

write(
    "packages/SystemUI/res/drawable/ic_a03_volume.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="M3,9v6h4l5,5V4L7,9H3zm13.5,3A4.5,4.5 0,0 0,14 7.97v8.05A4.5,4.5 0,0 0,16.5 12zm0,-8.24v2.06A7,7 0,0 1,20 12a7,7 0,0 1,-3.5 6.18v2.06A9,9 0,0 0,22 12a9,9 0,0 0,-5.5 -8.24z" />
</vector>
""",
)

view = "packages/SystemUI/src/com/android/systemui/settings/brightness/BrightnessSliderView.java"
replace_once(
    view,
    """    @NonNull
    private ToggleSeekBar mSlider;
""",
    """    @NonNull
    private ToggleSeekBar mSlider;
    @NonNull
    private ToggleSeekBar mVolumeSlider;
""",
)
replace_once(
    view,
    """        mSlider = requireViewById(R.id.slider);
        mSlider.setAccessibilityLabel(getContentDescription().toString());
""",
    """        mSlider = requireViewById(R.id.slider);
        mSlider.setAccessibilityLabel(getContentDescription().toString());
        mVolumeSlider = requireViewById(R.id.a03_volume_slider);
        mVolumeSlider.setAccessibilityLabel(
                getResources().getString(R.string.accessibility_volume_settings));
""",
)
replace_once(
    view,
    """    public void setOnSeekBarChangeListener(OnSeekBarChangeListener seekListener) {
        mSlider.setOnSeekBarChangeListener(seekListener);
    }
""",
    """    public void setOnSeekBarChangeListener(OnSeekBarChangeListener seekListener) {
        mSlider.setOnSeekBarChangeListener(seekListener);
    }

    public void setOnVolumeSeekBarChangeListener(OnSeekBarChangeListener seekListener) {
        mVolumeSlider.setOnSeekBarChangeListener(seekListener);
    }

    public void setVolumeMax(int max) {
        mVolumeSlider.setMax(max);
    }

    public void setVolumeValue(int value) {
        mVolumeSlider.setProgress(value);
    }
""",
)

controller = (
    "packages/SystemUI/src/com/android/systemui/settings/brightness/"
    "BrightnessSliderController.java"
)
replace_once(
    controller,
    """import android.content.Context;
import android.view.LayoutInflater;
""",
    """import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.media.AudioManager;
import android.view.LayoutInflater;
""",
)
replace_once(
    controller,
    """    private boolean mTracking;
    private final FalsingManager mFalsingManager;
""",
    """    private boolean mTracking;
    private final FalsingManager mFalsingManager;
    private final AudioManager mAudioManager;
    private boolean mVolumeReceiverRegistered;

    private final BroadcastReceiver mVolumeReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            refreshMediaVolume();
        }
    };
""",
)
replace_once(
    controller,
    """        mFalsingManager = falsingManager;
        mIcon = mView.findViewById(R.id.brightness_icon);
""",
    """        mFalsingManager = falsingManager;
        mIcon = mView.findViewById(R.id.brightness_icon);
        mAudioManager = mView.getContext().getSystemService(AudioManager.class);
        mView.setVolumeMax(mAudioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC));
        refreshMediaVolume();
""",
)
replace_once(
    controller,
    """    protected void onViewAttached() {
        mView.setOnSeekBarChangeListener(mSeekListener);
        mView.setOnInterceptListener(mOnInterceptListener);
    }

    @Override
    protected void onViewDetached() {
        mView.setOnSeekBarChangeListener(null);
        mView.setOnDispatchTouchEventListener(null);
        mView.setOnInterceptListener(null);
    }
""",
    """    protected void onViewAttached() {
        mView.setOnSeekBarChangeListener(mSeekListener);
        mView.setOnVolumeSeekBarChangeListener(mVolumeSeekListener);
        mView.setOnInterceptListener(mOnInterceptListener);
        refreshMediaVolume();
        if (!mVolumeReceiverRegistered) {
            mView.getContext().registerReceiver(mVolumeReceiver,
                    new IntentFilter("android.media.VOLUME_CHANGED_ACTION"),
                    Context.RECEIVER_NOT_EXPORTED);
            mVolumeReceiverRegistered = true;
        }
    }

    @Override
    protected void onViewDetached() {
        mView.setOnSeekBarChangeListener(null);
        mView.setOnVolumeSeekBarChangeListener(null);
        mView.setOnDispatchTouchEventListener(null);
        mView.setOnInterceptListener(null);
        if (mVolumeReceiverRegistered) {
            mView.getContext().unregisterReceiver(mVolumeReceiver);
            mVolumeReceiverRegistered = false;
        }
    }

    private void refreshMediaVolume() {
        mView.setVolumeValue(mAudioManager.getStreamVolume(AudioManager.STREAM_MUSIC));
    }
""",
)
replace_once(
    controller,
    """    /**
     * Creates a {@link BrightnessSliderController} with its associated view.
     */
""",
    """    private final SeekBar.OnSeekBarChangeListener mVolumeSeekListener =
            new SeekBar.OnSeekBarChangeListener() {
        @Override
        public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
            if (fromUser) {
                mAudioManager.setStreamVolume(AudioManager.STREAM_MUSIC, progress, 0);
            }
        }

        @Override
        public void onStartTrackingTouch(SeekBar seekBar) { }

        @Override
        public void onStopTrackingTouch(SeekBar seekBar) { }
    };

    /**
     * Creates a {@link BrightnessSliderController} with its associated view.
     */
""",
)

# ---------------------------------------------------------------------------
# Trebuchet: double-tap-to-sleep only on the empty Home workspace.
# Trebuchet is platform-signed so it can use PowerManager.goToSleep directly;
# there is no Accessibility service, overlay, widget or background helper app.
# ---------------------------------------------------------------------------
manifest = "packages/apps/Trebuchet/AndroidManifest-common.xml"
replace_once(
    manifest,
    """    <uses-permission android:name="android.permission.VIBRATE"/>
""",
    """    <uses-permission android:name="android.permission.VIBRATE"/>
    <uses-permission android:name="android.permission.DEVICE_POWER" />
""",
)

bp = "packages/apps/Trebuchet/Android.bp"
for module in ("Trebuchet", "TrebuchetGo", "TrebuchetQuickStep", "TrebuchetQuickStepGo"):
    marker = f'''android_app {{\n    name: "{module}",'''
    replacement = marker + '\n    certificate: "platform",'
    replace_once(bp, marker, replacement)

touch = "packages/apps/Trebuchet/src/com/android/launcher3/touch/WorkspaceTouchListener.java"
replace_once(
    touch,
    """import android.graphics.PointF;
import android.graphics.Rect;
""",
    """import android.graphics.PointF;
import android.graphics.Rect;
import android.os.PowerManager;
import android.os.SystemClock;
""",
)
replace_once(
    touch,
    """    private final float mTouchSlop;

    private int mLongPressState = STATE_CANCELLED;
""",
    """    private final float mTouchSlop;
    private final PowerManager mPowerManager;
    private long mLastEmptyTapTime;
    private final PointF mLastEmptyTapPoint = new PointF();

    private int mLongPressState = STATE_CANCELLED;
""",
)
replace_once(
    touch,
    """        mTouchSlop = 2 * ViewConfiguration.get(launcher).getScaledTouchSlop();
        mGestureDetector = new GestureDetector(workspace.getContext(), this);
""",
    """        mTouchSlop = 2 * ViewConfiguration.get(launcher).getScaledTouchSlop();
        mPowerManager = launcher.getSystemService(PowerManager.class);
        mGestureDetector = new GestureDetector(workspace.getContext(), this);
""",
)
replace_once(
    touch,
    """        if (action == ACTION_UP || action == ACTION_POINTER_UP) {
            if (!mWorkspace.isHandlingTouch()) {
""",
    """        if (action == ACTION_UP && !mWorkspace.isHandlingTouch()
                && canHandleLongPress()
                && ev.getEventTime() - ev.getDownTime()
                        < ViewConfiguration.getLongPressTimeout()) {
            final long now = ev.getEventTime();
            final boolean closeInTime = now - mLastEmptyTapTime
                    <= ViewConfiguration.getDoubleTapTimeout();
            final boolean closeInSpace = PointF.length(
                    mLastEmptyTapPoint.x - ev.getX(),
                    mLastEmptyTapPoint.y - ev.getY()) <= mTouchSlop;
            if (closeInTime && closeInSpace) {
                mLastEmptyTapTime = 0;
                cancelLongPress();
                mPowerManager.goToSleep(SystemClock.uptimeMillis());
                return true;
            }
            mLastEmptyTapTime = now;
            mLastEmptyTapPoint.set(ev.getX(), ev.getY());
        }

        if (action == ACTION_UP || action == ACTION_POINTER_UP) {
            if (!mWorkspace.isHandlingTouch()) {
""",
)

# ---------------------------------------------------------------------------
# Minimal official Google core: Play Store, Play services, framework, account
# partner setup and contact/calendar sync. Remove user-facing Google extras.
# ---------------------------------------------------------------------------
replace_once(
    "vendor/gapps/arm64/arm64-vendor.mk",
    """PRODUCT_PACKAGES += \\
    GmsCore \\
    Phonesky

ifeq ($(TARGET_IS_GROUPER),)

PRODUCT_PACKAGES += \\
    MarkupGoogle \\
    SpeechServicesByGoogle \\
    talkback \\
    Velvet \\
    SetupWizard
endif
""",
    """# A03 LiteOS core-only Google package set.
PRODUCT_PACKAGES += \\
    GmsCore \\
    Phonesky
""",
)
replace_once(
    "vendor/gapps/common/common-vendor.mk",
    """PRODUCT_PACKAGES += \\
    GoogleCalendarSyncAdapter \\
    GoogleContactsSyncAdapter \\
    PrebuiltExchange3Google \\
    AndroidAutoStub \\
    GooglePartnerSetup \\
    GoogleFeedback \\
    GoogleServicesFramework \\
    com.google.android.dialer.support

ifeq ($(TARGET_IS_GROUPER),)

PRODUCT_PACKAGES += \\
    GoogleRestore
endif
""",
    """# Only background components needed for Play and account/contact sync.
PRODUCT_PACKAGES += \\
    GoogleCalendarSyncAdapter \\
    GoogleContactsSyncAdapter \\
    GooglePartnerSetup \\
    GoogleServicesFramework
""",
)

print("A03 LiteOS source patches applied successfully")
