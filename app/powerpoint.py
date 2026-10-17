"""Attach-only Windows PowerPoint adapter. Never opens, edits, saves, or quits decks.

Use on the UI/main thread. GotoSlide navigates slides rather than animation
steps. Read-back confirms the displayed slide index, not rendered pixels.
"""

from dataclasses import dataclass
import sys
from time import perf_counter


class PowerPointError(RuntimeError):
    pass


class PowerPointCommandError(PowerPointError):
    """A rejected command which does not invalidate a healthy connection."""


@dataclass(frozen=True)
class PresentationState:
    name: str
    slide: int
    count: int


@dataclass(frozen=True)
class ActionResult:
    state: PresentationState
    moved: bool
    elapsed_ms: float


def active_powerpoint():
    if sys.platform != "win32":
        raise PowerPointError("PowerPoint integration requires Windows desktop PowerPoint.")
    try:
        import win32com.client
    except ImportError as exc:
        raise PowerPointError("Install prototype dependencies again; pywin32 is missing.") from exc
    try:
        return win32com.client.GetActiveObject("PowerPoint.Application")
    except Exception as exc:
        raise PowerPointError("Open PowerPoint and start your slideshow, then click Connect.") from exc


class PowerPointAdapter:
    def __init__(self, app_factory=None):
        self._factory = app_factory or active_powerpoint
        self.disconnect()

    def disconnect(self):
        self._app = None
        self._show_identity = None
        self._name = None

    def connect(self):
        self.disconnect()
        try:
            app = self._factory()
            count = int(app.SlideShowWindows.Count)
            if count != 1:
                raise PowerPointError("Start exactly one PowerPoint slideshow before connecting.")
            window = app.SlideShowWindows.Item(1)
            self._validate_show(window)
            self._app = app
            self._show_identity = self._identity(window)
            self._name = str(window.Presentation.FullName)
            return self._state(window)
        except PowerPointError:
            self.disconnect()
            raise
        except Exception as exc:
            self.disconnect()
            raise PowerPointError("PowerPoint is unavailable or busy. Close dialogs and reconnect.") from exc

    @staticmethod
    def _identity(window):
        # SlideShowWindow.HWND is not implemented by all Office versions.
        # COM's canonical IUnknown identity binds this exact show object instead.
        if hasattr(window, "_oleobj_"):
            import pythoncom
            return window._oleobj_.QueryInterface(pythoncom.IID_IUnknown)
        return id(window)  # injectable non-COM fixtures, compared by identity

    @staticmethod
    def _validate_show(window):
        # Range/custom shows have their own order; do not guess their navigation.
        if int(window.Presentation.SlideShowSettings.RangeType) != 1:
            raise PowerPointError("Use 'All slides' in PowerPoint Set Up Slide Show; custom/range shows are not supported yet.")

    def _window(self):
        if self._app is None:
            raise PowerPointError("PowerPoint is not connected. Start its slideshow and click Connect.")
        for index in range(1, int(self._app.SlideShowWindows.Count) + 1):
            window = self._app.SlideShowWindows.Item(index)
            if self._identity(window) == self._show_identity and str(window.Presentation.FullName) == self._name:
                self._validate_show(window)
                return window
        raise PowerPointError("The connected slideshow ended or changed. Connect again before sending commands.")

    @staticmethod
    def _state(window):
        return PresentationState(str(window.Presentation.Name), int(window.View.Slide.SlideIndex),
                                 int(window.Presentation.Slides.Count))

    def snapshot(self):
        try:
            return self._state(self._window())
        except PowerPointError:
            self.disconnect()
            raise
        except Exception as exc:
            self.disconnect()
            raise PowerPointError("Cannot read the PowerPoint slideshow. Close dialogs and reconnect.") from exc

    def apply(self, action, target_slide=None):
        started = perf_counter()
        try:
            window = self._window()
            before = self._state(window)
            slides = window.Presentation.Slides
            if action == "goto":
                if type(target_slide) is not int or not 1 <= target_slide <= before.count:
                    raise PowerPointCommandError(f"Slide number must be between 1 and {before.count}.")
                target = target_slide
            elif action in ("next", "previous"):
                direction = 1 if action == "next" else -1
                target = before.slide
                for candidate in range(before.slide + direction,
                                       before.count + 1 if direction == 1 else 0, direction):
                    if not bool(slides.Item(candidate).SlideShowTransition.Hidden):
                        target = candidate
                        break
            else:
                raise PowerPointCommandError(f"Unsupported PowerPoint action: {action}")
            if target != before.slide:
                window.View.GotoSlide(target, 0)  # msoFalse: preserve animation progress on return
            after = self._state(window)
            if after.slide != target:
                raise PowerPointError("PowerPoint did not confirm the requested slide. Check the slideshow and reconnect.")
            return ActionResult(after, after.slide != before.slide, (perf_counter() - started) * 1000)
        except PowerPointCommandError:
            raise
        except PowerPointError:
            # Invalidate the binding on failure; never silently route to another show.
            self.disconnect()
            raise
        except Exception as exc:
            self.disconnect()
            raise PowerPointError("PowerPoint command failed. Check for dialogs or a closed slideshow, then reconnect.") from exc
