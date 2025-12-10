# GUI Styles and Theme Configuration
"""
styles - Dark theme configuration for the Mini Synthesizer GUI.

Provides consistent colors, fonts, and styling for tkinter/ttk widgets.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any


# Color Palette (Dark Theme)
COLORS: Dict[str, str] = {
    # Backgrounds
    'bg_dark': '#1a1a1a',
    'bg_panel': '#252525',
    'bg_widget': '#2d2d2d',
    'bg_input': '#1f1f1f',

    # Foregrounds
    'fg_primary': '#e0e0e0',
    'fg_secondary': '#a0a0a0',
    'fg_muted': '#606060',

    # Accents
    'accent_primary': '#00b4d8',
    'accent_secondary': '#0096c7',
    'accent_hover': '#48cae4',

    # Functional colors
    'success': '#00ff88',
    'warning': '#fbbf24',
    'error': '#f87171',
    'record': '#ef4444',

    # Component colors
    'key_white': '#f0f0f0',
    'key_black': '#1a1a1a',
    'key_pressed': '#00b4d8',
    'grid': '#333333',
    'waveform': '#00ff88',
    'filter_curve': '#ff6b6b',

    # Borders
    'border': '#404040',
    'border_focus': '#00b4d8',
}

# Font Configuration
FONTS: Dict[str, tuple] = {
    'title': ('Segoe UI', 11, 'bold'),
    'label': ('Segoe UI', 9),
    'value': ('Consolas', 9),
    'small': ('Segoe UI', 8),
    'large_value': ('Consolas', 14),
    'heading': ('Segoe UI', 12, 'bold'),
}

# Dimension Constants
DIMENSIONS: Dict[str, int] = {
    'padding_small': 4,
    'padding_medium': 8,
    'padding_large': 16,
    'border_width': 1,
    'slider_length': 150,
    'panel_width': 400,
    'window_width': 1280,
    'window_height': 800,
    'min_window_width': 1024,
    'min_window_height': 768,
}


def configure_dark_theme(root: tk.Tk) -> ttk.Style:
    """
    Configure the dark theme for the application.

    Args:
        root: The root tkinter window

    Returns:
        The configured ttk.Style object
    """
    style = ttk.Style(root)

    # Try to use a theme that supports customization
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass  # Fall back to default theme

    # Configure general styles
    style.configure(
        '.',
        background=COLORS['bg_dark'],
        foreground=COLORS['fg_primary'],
        font=FONTS['label']
    )

    # Frame styles
    style.configure(
        'Dark.TFrame',
        background=COLORS['bg_dark']
    )

    style.configure(
        'Panel.TFrame',
        background=COLORS['bg_panel']
    )

    # LabelFrame styles
    style.configure(
        'Dark.TLabelframe',
        background=COLORS['bg_panel'],
        foreground=COLORS['fg_primary'],
        bordercolor=COLORS['border'],
        lightcolor=COLORS['border'],
        darkcolor=COLORS['border']
    )

    style.configure(
        'Dark.TLabelframe.Label',
        background=COLORS['bg_panel'],
        foreground=COLORS['accent_primary'],
        font=FONTS['title']
    )

    # Label styles
    style.configure(
        'Dark.TLabel',
        background=COLORS['bg_dark'],
        foreground=COLORS['fg_primary'],
        font=FONTS['label']
    )

    style.configure(
        'Title.TLabel',
        background=COLORS['bg_dark'],
        foreground=COLORS['accent_primary'],
        font=FONTS['title']
    )

    style.configure(
        'Value.TLabel',
        background=COLORS['bg_dark'],
        foreground=COLORS['fg_secondary'],
        font=FONTS['value']
    )

    style.configure(
        'Panel.TLabel',
        background=COLORS['bg_panel'],
        foreground=COLORS['fg_primary'],
        font=FONTS['label']
    )

    # Button styles
    style.configure(
        'Dark.TButton',
        background=COLORS['bg_widget'],
        foreground=COLORS['fg_primary'],
        bordercolor=COLORS['border'],
        focuscolor=COLORS['accent_primary'],
        font=FONTS['label'],
        padding=(8, 4)
    )

    style.map(
        'Dark.TButton',
        background=[
            ('active', COLORS['bg_panel']),
            ('pressed', COLORS['accent_secondary'])
        ],
        foreground=[
            ('active', COLORS['fg_primary'])
        ]
    )

    style.configure(
        'Accent.TButton',
        background=COLORS['accent_primary'],
        foreground='#ffffff',
        bordercolor=COLORS['accent_secondary'],
        focuscolor=COLORS['accent_hover'],
        font=FONTS['label'],
        padding=(8, 4)
    )

    style.map(
        'Accent.TButton',
        background=[
            ('active', COLORS['accent_hover']),
            ('pressed', COLORS['accent_secondary'])
        ]
    )

    style.configure(
        'Record.TButton',
        background=COLORS['record'],
        foreground='#ffffff',
        bordercolor='#dc2626',
        font=FONTS['label'],
        padding=(8, 4)
    )

    style.map(
        'Record.TButton',
        background=[
            ('active', '#dc2626'),
            ('pressed', '#b91c1c')
        ]
    )

    # Scale (slider) styles
    style.configure(
        'Dark.Horizontal.TScale',
        background=COLORS['bg_dark'],
        troughcolor=COLORS['bg_input'],
        sliderrelief='flat'
    )

    style.configure(
        'Dark.Vertical.TScale',
        background=COLORS['bg_dark'],
        troughcolor=COLORS['bg_input'],
        sliderrelief='flat'
    )

    # Combobox styles
    style.configure(
        'Dark.TCombobox',
        background=COLORS['bg_input'],
        foreground=COLORS['fg_primary'],
        fieldbackground=COLORS['bg_input'],
        selectbackground=COLORS['accent_primary'],
        selectforeground='#ffffff',
        arrowcolor=COLORS['fg_primary']
    )

    style.map(
        'Dark.TCombobox',
        fieldbackground=[('readonly', COLORS['bg_input'])],
        selectbackground=[('readonly', COLORS['accent_primary'])]
    )

    # Radiobutton styles
    style.configure(
        'Dark.TRadiobutton',
        background=COLORS['bg_dark'],
        foreground=COLORS['fg_primary'],
        font=FONTS['small']
    )

    style.map(
        'Dark.TRadiobutton',
        background=[
            ('active', COLORS['bg_panel'])
        ]
    )

    # Checkbutton styles
    style.configure(
        'Dark.TCheckbutton',
        background=COLORS['bg_dark'],
        foreground=COLORS['fg_primary'],
        font=FONTS['label']
    )

    style.map(
        'Dark.TCheckbutton',
        background=[
            ('active', COLORS['bg_panel'])
        ]
    )

    # Spinbox styles
    style.configure(
        'Dark.TSpinbox',
        background=COLORS['bg_input'],
        foreground=COLORS['fg_primary'],
        fieldbackground=COLORS['bg_input'],
        arrowcolor=COLORS['fg_primary']
    )

    # Separator styles
    style.configure(
        'Dark.TSeparator',
        background=COLORS['border']
    )

    # Notebook (tab) styles
    style.configure(
        'Dark.TNotebook',
        background=COLORS['bg_dark'],
        bordercolor=COLORS['border']
    )

    style.configure(
        'Dark.TNotebook.Tab',
        background=COLORS['bg_panel'],
        foreground=COLORS['fg_primary'],
        padding=(12, 4),
        font=FONTS['label']
    )

    style.map(
        'Dark.TNotebook.Tab',
        background=[
            ('selected', COLORS['bg_dark']),
            ('active', COLORS['bg_widget'])
        ],
        foreground=[
            ('selected', COLORS['accent_primary'])
        ]
    )

    # Progressbar styles
    style.configure(
        'Dark.Horizontal.TProgressbar',
        background=COLORS['accent_primary'],
        troughcolor=COLORS['bg_input']
    )

    return style


def create_panel_frame(parent: tk.Widget, title: str = None) -> ttk.LabelFrame:
    """
    Create a styled panel frame with optional title.

    Args:
        parent: Parent widget
        title: Optional title for the panel

    Returns:
        Styled LabelFrame widget
    """
    if title:
        frame = ttk.LabelFrame(
            parent,
            text=title,
            style='Dark.TLabelframe',
            padding=DIMENSIONS['padding_large']
        )
    else:
        frame = ttk.Frame(parent, style='Dark.TFrame')

    return frame


def create_slider_with_label(
    parent: tk.Widget,
    label_text: str,
    variable: tk.Variable,
    from_: float,
    to: float,
    orient: str = 'horizontal',
    length: int = None,
    value_format: str = '{:.2f}',
    command: callable = None
) -> tuple:
    """
    Create a slider with label and value display.

    Args:
        parent: Parent widget
        label_text: Label text
        variable: tkinter variable to bind
        from_: Minimum value
        to: Maximum value
        orient: 'horizontal' or 'vertical'
        length: Slider length in pixels
        value_format: Format string for value display
        command: Callback function

    Returns:
        Tuple of (container_frame, label, slider, value_label)
    """
    if length is None:
        length = DIMENSIONS['slider_length']

    container = ttk.Frame(parent, style='Dark.TFrame')

    label = ttk.Label(
        container,
        text=label_text,
        style='Dark.TLabel'
    )

    style_name = f'Dark.{orient.capitalize()}.TScale'

    value_label = ttk.Label(
        container,
        text=value_format.format(variable.get()),
        style='Value.TLabel',
        width=8
    )

    def on_change(val):
        value_label.config(text=value_format.format(float(val)))
        if command:
            command(float(val))

    slider = ttk.Scale(
        container,
        from_=from_,
        to=to,
        variable=variable,
        orient=orient,
        length=length,
        style=style_name,
        command=on_change
    )

    if orient == 'horizontal':
        label.pack(side='left', padx=(0, 8))
        slider.pack(side='left', fill='x', expand=True)
        value_label.pack(side='right', padx=(8, 0))
    else:
        label.pack(side='top')
        slider.pack(side='top', pady=4)
        value_label.pack(side='top')

    return container, label, slider, value_label


class ColorScheme:
    """Convenience class for accessing color values."""

    bg_dark = COLORS['bg_dark']
    bg_panel = COLORS['bg_panel']
    bg_widget = COLORS['bg_widget']
    bg_input = COLORS['bg_input']

    fg_primary = COLORS['fg_primary']
    fg_secondary = COLORS['fg_secondary']
    fg_muted = COLORS['fg_muted']

    accent = COLORS['accent_primary']
    accent_hover = COLORS['accent_hover']

    success = COLORS['success']
    warning = COLORS['warning']
    error = COLORS['error']
    record = COLORS['record']

    key_white = COLORS['key_white']
    key_black = COLORS['key_black']
    key_pressed = COLORS['key_pressed']

    waveform = COLORS['waveform']
    filter_curve = COLORS['filter_curve']
    grid = COLORS['grid']
    border = COLORS['border']
