import tkinter as tk
from tkinter import ttk, messagebox

class BaseQuestionnaire:
    '''Base class for questionnaires. Subclasses should implement the add_questions and submit methods.'''

    def __init__(self, title, subtitle):
        # Create main window
        self.root = tk.Tk()
        self.root.focus_force()
        self.root.title("Questionnaire")
        self.root.state('zoomed')

        self.title_text = title
        self.subtitle_text = subtitle
        self.responses = None

    def setup_ui(self):
        '''Sets up the UI layout with a header, a scrollable area for questions, and a footer with a submit button.'''
        self.setup_header()
        self.create_scrollable_frame()
        self.setup_footer()

    def setup_header(self):
        '''Sets up the header of the questionnaire with a title and subtitle. 
        The header is fixed at the top of the window.
        '''
        # Header frame (fixed at top)
        header_frame = tk.Frame(self.root, height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        # Title
        title = tk.Label(
            header_frame, 
            text=self.title_text,
            font=('Arial', 20, 'bold')
        )
        title.pack(pady=(15, 5))
        
        # Subtitle
        subtitle = tk.Label(
            header_frame,
            text=self.subtitle_text,
            font=('Arial', 11)
        )
        subtitle.pack()

    def setup_footer(self):
        '''Sets up the footer of the questionnaire with a submit button.
        The footer is fixed at the bottom of the window.
        '''
        # Footer frame (fixed at bottom)
        footer_frame = tk.Frame(self.root, height=70)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        # Submit button
        self.submit_button = tk.Button(
            footer_frame,
            text="Submit Responses",
            font=('Arial', 13, 'bold'),
            padx=40,
            pady=12,
            command=self.submit,
            cursor='hand2',
            relief=tk.FLAT
        )
        self.submit_button.pack(pady=15)
    
    def create_scrollable_frame(self):
        '''Creates a scrollable frame for the questions.
        The scrollable frame is placed between the header and footer and expands to fill the available space.
        '''
        # Container for canvas and scrollbar
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Canvas
        canvas = tk.Canvas(container)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame inside canvas
        scrollable_frame = tk.Frame(canvas)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        
        # Configure scrolling
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            # Make the frame width match canvas width
            canvas.itemconfig(canvas_frame, width=canvas.winfo_width())
        
        scrollable_frame.bind('<Configure>', configure_scroll_region)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_frame, width=e.width))
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Add questions to scrollable frame
        self.add_questions(scrollable_frame)

    def add_questions(self, parent):
        '''Adds questions to the given parent frame. Subclasses must implement this method.'''
        raise NotImplementedError("Subclasses must implement add_questions method")
    
    def submit(self):
        '''Handles the submission of responses. Subclasses must implement this method.'''
        raise NotImplementedError("Subclasses must implement submit method")
    
    def run(self):
        '''Runs the questionnaire by launching the GUI event loop. 
        Returns the collected responses after submission.
        '''
        # Start the GUI event loop
        self.root.mainloop()
        return getattr(self, 'responses', None)
    
class SliderQuestionnaire(BaseQuestionnaire):
    '''Implements a questionnaire where each question is answered using a slider.
    The questionnaire is organized into categories, and each category has its own section in the UI.
    The responses are collected in a dictionary mapping question text to the selected slider value.
    The sliders are initialized to the middle position (3) but are marked as unanswered until the user interacts with them. 
    The submit button checks that all questions have been answered before allowing submission.
    '''

    def __init__(self, questions, camera):
        self.camera = camera
        self.questions = questions
        self.sliders = []
        self.slider_labels = []

        title = f"Questionnaire for {camera.replace('_', ' ').title()}"
        subtitle = "Please rate your agreement with each statement using the sliders below"

        super().__init__(title, subtitle)
        self.setup_ui()

    def add_questions(self, parent):
        '''Adds questions to the questionnaire UI, organized by category. 
        Each category is displayed in a separate section with a header.
        '''
        question_index = 0
        for category in self.questions.keys():
            # Category frame
            category_frame = tk.LabelFrame(
                parent,
                text=category.replace('_', ' ').title(),
                font=('Arial', 14, 'bold')
            )
            category_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
            
            # Add questions for this category
            for question in self.questions[category]:
                self._add_single_question(category_frame, question, question_index)
                question_index += 1

    def _add_single_question(self, parent, question, index):
        '''Adds a single question to the given parent frame.'''
        # Question container
        question_frame = tk.Frame(parent, bg='white', relief=tk.FLAT, bd=1)
        question_frame.pack(fill=tk.X, padx=30, pady=10)
        
        # Inner padding
        inner_frame = tk.Frame(question_frame, bg='white')
        inner_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Question number and text
        q_text = tk.Label(
            inner_frame,
            text=f"Question {index+1}: {question}",
            font=('Arial', 12),
            bg='white',
            wraplength=650,
            justify='left',
            anchor='w'
        )
        q_text.pack(fill=tk.X, pady=(0, 15))
        
        # Container for slider area
        slider_area = tk.Frame(inner_frame, bg='white')
        slider_area.pack(fill=tk.X)
        
        # Left side: slider components
        slider_left = tk.Frame(slider_area, bg='white')
        slider_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scale labels frame (with fixed width to match slider)
        labels_frame = tk.Frame(slider_left, bg='white')
        labels_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Left label
        tk.Label(
            labels_frame,
            text="Strongly Disagree",
            font=('Arial', 9),
            bg='white',
            fg='gray'
        ).pack(side=tk.LEFT)
        
        # Right label
        tk.Label(
            labels_frame,
            text="Strongly Agree",
            font=('Arial', 9),
            bg='white',
            fg='gray'
        ).pack(side=tk.RIGHT)
        
        # Create slider
        slider = tk.Scale(
            slider_left,
            from_=1,
            to=5,
            orient=tk.HORIZONTAL,
            showvalue=0,
            length=450,
            sliderlength=30,
            bg='white',
            troughcolor='#e0e0e0'
        )
        slider.pack(fill=tk.X)
        
        # Set to middle position but mark as not answered
        slider.set(3)
        slider.answered = False
        
        self.sliders.append(slider)

        # Right side: Value label (shows current selection)
        value_label = tk.Label(
            slider_area,
            text="Not answered",
            font=('Arial', 13, 'bold'),
            bg='white',
            width=15
        )
        value_label.pack(side=tk.RIGHT, padx=(20, 0))
        self.slider_labels.append(value_label)

        slider.configure(command=lambda val, idx=index: self._on_slider_change(val, idx))
            
    def _on_slider_change(self, value, index):
        '''Handles changes to the slider value.'''
        # Mark slider as answered
        self.sliders[index].answered = True
        
        # Update value label
        value = int(float(value))
        labels = {
            1: "Strongly Disagree",
            2: "Disagree",
            3: "Neutral",
            4: "Agree",
            5: "Strongly Agree"
        }
        
        self.slider_labels[index].config(
            text=labels[value]
        )

    def submit(self):
        ''''Handles the submission of responses. 
        Checks that all questions have been answered and collects the responses into a dictionary.
        '''
        # Check if all questions are answered
        unanswered = [i + 1 for i, slider in enumerate(self.sliders) if not slider.answered]
        
        if unanswered:
            messagebox.showwarning(
                "Incomplete Questionnaire",
                f"Please answer all questions.\n\nUnanswered: Question(s) {', '.join(map(str, unanswered))}"
            )
            return
        
        # Flatten the questions dictionary to get all question texts
        all_questions = [q for category in self.questions.values() for q in category]

        # Collect responses
        self.responses = {question: slider.get() for question, slider in zip(all_questions, self.sliders)}

        # Close
        self.root.destroy()

class RadioButtonQuestionnaire(BaseQuestionnaire):
    '''Implements a questionnaire where each question is answered using radio buttons.
    Each question corresponds to a shape, and the user selects their preferred camera perspective for that shape.
    The responses are collected in a dictionary mapping shape name to the selected camera perspective.
    The submit button checks that all shapes have a selection before allowing submission.
    '''
    
    def __init__(self, questions, shapes):
        self.questions = questions
        self.shapes = shapes
        self.shape_vars = {}

        title = "Camera Preference Questionnaire"
        subtitle = "Please select one option for each question below"

        super().__init__(title, subtitle)
        self.setup_ui()

    def add_questions(self, parent):
        '''Adds questions to the questionnaire UI.'''
        # Create a single section for all shapes since the question is the same for each shape
        q_frame = tk.LabelFrame(
            parent,
            text="Preference",
            font=('Arial', 14, 'bold')
        )
        q_frame.pack(fill=tk.X, padx=30, pady=(20, 10))

        # Question container
        question_frame = tk.Frame(q_frame, bg='white', relief=tk.FLAT, bd=1)
        question_frame.pack(fill=tk.X, padx=30, pady=10)
        
        # Inner padding
        inner_frame = tk.Frame(question_frame, bg='white')
        inner_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Question text
        q_text = tk.Label(
            inner_frame,
            text=self.questions[0],
            font=('Arial', 12),
            bg='white',
            wraplength=650,
            justify='left',
            anchor='w'
        )
        q_text.pack(fill=tk.X, pady=(0, 15))
        
        # Table container
        table_frame = tk.Frame(inner_frame, bg='white')
        table_frame.pack(fill=tk.X)
        
        # Create table-like layout for each shape
        for i, shape in enumerate(self.shapes):
            self._add_radio_row(table_frame, shape)
    
    def _add_radio_row(self, parent, shape):
        '''Adds a row of radio buttons for a specific shape. 
        Each row contains the shape name and two radio buttons for camera preference.
        '''
        # Row frame for each shape
        row_frame = tk.Frame(parent, bg='white')
        row_frame.pack(fill=tk.X, pady=5)
        
        # Shape name label (left column)
        shape_label = tk.Label(
            row_frame,
            text=f"{shape}:",
            font=('Arial', 11, 'bold'),
            bg='white',
            width=15,
            anchor='w'
        )
        shape_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Radio buttons variable for this shape
        self.shape_vars[shape] = tk.StringVar()
        
        # Stationary camera radio button
        tk.Radiobutton(
            row_frame,
            text="Stationary Camera",
            variable=self.shape_vars[shape],
            value="stationary_cam",
            font=('Arial', 10),
            bg='white',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 30))
        
        # Dynamic camera radio button
        tk.Radiobutton(
            row_frame,
            text="Dynamic Camera",
            variable=self.shape_vars[shape],
            value="dynamic_cam",
            font=('Arial', 10),
            bg='white',
            cursor='hand2'
        ).pack(side=tk.LEFT)

    def submit(self):
        '''Handles the submission of responses. 
        Checks that all shapes have a selection and collects the responses into a dictionary.
        '''
        # Check if all shapes have a selection
        unanswered_shapes = [shape for shape in self.shapes if not self.shape_vars[shape].get()]
        
        if unanswered_shapes:
            messagebox.showwarning(
                "Incomplete Questionnaire",
                f"Please answer for all shapes.\n\nUnanswered: {', '.join(unanswered_shapes)}"
            )
            return
        
        # Collect responses
        self.responses = {shape: var.get() for shape, var in self.shape_vars.items()}
        
        # Close
        self.root.destroy()