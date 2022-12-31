from django.forms.widgets import Input


class TotalDifficultyInput(Input):
    input_type = "number"
    template_name = "main/widgets/total_difficulty.html"
