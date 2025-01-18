from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.pymongo import ModelView
from flask_admin.form import FileUploadField
from wtforms import form, fields
from wtforms.widgets import ListWidget, CheckboxInput, html_params
from wtforms.validators import DataRequired
from markupsafe import Markup
from app.models.s3_utils import S3Uploader
from app.models.utils import get_current_time
from app.config import mongo

admin = Admin(name='Restaurant Admin', template_mode='bootstrap4')
s3_uploader = S3Uploader()

# Add this new class for image preview widget
class ImagePreviewWidget:
    def __call__(self, field, **kwargs):
        html = []
        if field._urls:  # Show existing images
            html.append('<div class="existing-images">')
            html.append('<label>Current Images:</label>')
            html.append('<div class="image-preview">')
            for url in field._urls:
                html.append(f'<img src="{url}" alt="Preview">')
            html.append('</div>')
            html.append('</div>')
        
        # Add file input for new images
        kwargs['multiple'] = True
        kwargs['accept'] = 'image/*'
        html.append(f'<input type="file" name="{field.name}" **{html_params(**kwargs)}>')
        return Markup(''.join(html))

# Update MultipleFileField to use the custom widget
class MultipleFileField(fields.FileField):
    widget = ImagePreviewWidget()

    def __init__(self, label=None, validators=None, **kwargs):
        super(MultipleFileField, self).__init__(label, validators, **kwargs)
        self._urls = []

    def process_formdata(self, valuelist):
        self.data = valuelist

    def process_data(self, value):
        if isinstance(value, list):
            self._urls = value
            self.data = value

    def _value(self):
        return self._urls if self._urls else []

# Add this new class for custom widget
class InlineCheckboxWidget(ListWidget):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = [f'<div class="form-group"><label class="control-label">{field.label.text}</label>']
        html.append('<div class="hashtag-wrapper">')
        html.append('<div class="hashtag-grid">')
        for subfield in field:
            html.append('<div class="hashtag-item">')
            html.append(f'<label class="checkbox-inline">{subfield()} {subfield.label.text}</label>')
            html.append('</div>')
        html.append('</div>')
        html.append('</div>')
        html.append('</div>')
        return Markup(''.join(html))

# Add LogoPreviewWidget after ImagePreviewWidget
class LogoPreviewWidget:
    def __call__(self, field, **kwargs):
        html = []
        if field.data and isinstance(field.data, str):  # Show existing logo
            html.append('<div class="existing-images">')
            html.append('<label>Current Logo:</label>')
            html.append('<div class="image-preview">')
            html.append(f'<img src="{field.data}" alt="Logo Preview">')
            html.append('</div>')
            html.append('</div>')
        
        # Add file input for new logo
        kwargs['accept'] = 'image/*'
        html.append(f'<input type="file" name="{field.name}" {html_params(**kwargs)}>')
        return Markup(''.join(html))

# Add custom logo field
class LogoField(fields.FileField):
    widget = LogoPreviewWidget()

    def _value(self):
        return self.data if self.data else ''

class AdminHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

def get_hashtag_choices():
    # Get all hashtags from MongoDB
    hashtags = list(mongo.db.hashtags.find())
    # Return list of tuples (id, name) for SelectMultipleField
    return [(str(hashtag['_id']), hashtag['name']) for hashtag in hashtags]

class RestaurantForm(form.Form):
    name = fields.StringField('Name', [DataRequired()])
    phone = fields.StringField('Phone', [DataRequired()])
    shortLocation = fields.StringField('Short Location', [DataRequired()])
    description = fields.TextAreaField('Description', [DataRequired()])
    priceRange = fields.SelectField('Price Range', 
                                  choices=[('$', '$'), ('$$', '$$'), ('$$$', '$$$')],
                                  validators=[DataRequired()])
    url = fields.StringField('URL', [DataRequired()])
    latitude = fields.FloatField('Latitude', default=0)
    longitude = fields.FloatField('Longitude', default=0)
    hashtags = fields.SelectMultipleField('Hashtags', 
                                        choices=get_hashtag_choices,
                                        widget=InlineCheckboxWidget(),
                                        option_widget=CheckboxInput())
    logo = LogoField('Logo')
    images = MultipleFileField('Images')
    menuImages = MultipleFileField('Menu Images')

class RestaurantsView(ModelView):
    column_list = ('name', 'phone', 'shortLocation', 'priceRange', 'rating')
    column_sortable_list = ('name', 'rating')
    form = RestaurantForm
    
    def _handle_file_upload(self, file, folder, restaurant_name=None):
        """Handle file upload to S3"""
        if not file:
            return None
        if isinstance(file, str):
            return file  # Return existing URL
        return s3_uploader.upload_file(file, folder, restaurant_name)
    
    def edit_form(self, obj=None):
        """Populate form with existing data when editing"""
        form = super(RestaurantsView, self).edit_form(obj)
        if obj:
            # Show existing images in the form
            if 'images' in obj and obj['images']:
                print(f"Setting existing images: {obj['images']}")
                form.images.process_data(obj['images'])
            if 'menuImages' in obj and obj['menuImages']:
                print(f"Setting existing menu images: {obj['menuImages']}")
                form.menuImages.process_data(obj['menuImages'])
        return form

    def on_model_change(self, form, model, is_created):
        try:
            # Get restaurant name for folder structure
            restaurant_name = model.get('name')
            
            # Create a clean model dictionary
            clean_model = {
                'name': model.get('name'),
                'phone': model.get('phone'),
                'shortLocation': model.get('shortLocation'),
                'description': model.get('description'),
                'priceRange': model.get('priceRange'),
                'url': model.get('url'),
                'latitude': float(model.get('latitude', 0)),
                'longitude': float(model.get('longitude', 0)),
                'hashtags': model.get('hashtags', []),
                'rating': model.get('rating', 0),
                'reviewCount': model.get('reviewCount', 0)
            }

            # Handle logo upload
            if form.logo.data:
                if isinstance(form.logo.data, str):
                    clean_model['logo'] = form.logo.data
                else:
                    logo_url = self._handle_file_upload(form.logo.data, 'logos', restaurant_name)
                    if logo_url:
                        clean_model['logo'] = logo_url
            
            # Handle images upload
            if form.images.data:
                image_urls = []
                if isinstance(form.images.data, list):
                    for image in form.images.data:
                        if isinstance(image, str):
                            image_urls.append(image)
                        elif image and hasattr(image, 'filename'):
                            url = self._handle_file_upload(image, 'images', restaurant_name)
                            if url:
                                image_urls.append(url)
                if image_urls:
                    clean_model['images'] = image_urls
            
            # Handle menu images upload
            if form.menuImages.data:
                menu_urls = []
                if isinstance(form.menuImages.data, list):
                    for menu in form.menuImages.data:
                        if isinstance(menu, str):
                            menu_urls.append(menu)
                        elif menu and hasattr(menu, 'filename'):
                            url = self._handle_file_upload(menu, 'menus', restaurant_name)
                            if url:
                                menu_urls.append(url)
                if menu_urls:
                    clean_model['menuImages'] = menu_urls

            # Set timestamps
            if is_created:
                clean_model['createdAt'] = clean_model['updatedAt'] = get_current_time()
            else:
                clean_model['updatedAt'] = get_current_time()
            
            # Update the original model with clean data
            model.clear()
            model.update(clean_model)
                
        except Exception as e:
            print(f"Error in on_model_change: {str(e)}")
            raise

    def create_form(self, obj=None):
        form = super(RestaurantsView, self).create_form(obj)
        form.hashtags.choices = get_hashtag_choices()
        return form

    def edit_form(self, obj=None):
        form = super(RestaurantsView, self).edit_form(obj)
        form.hashtags.choices = get_hashtag_choices()
        return form

    def create_blueprint(self, admin):
        blueprint = super(RestaurantsView, self).create_blueprint(admin)
        blueprint.extra_js = [
            """
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // Handle file input change for multiple files
                    function handleFileSelect(event) {
                        const input = event.target;
                        const preview = input.parentElement.querySelector('.image-preview');
                        
                        if (!preview) {
                            const newPreview = document.createElement('div');
                            newPreview.className = 'image-preview';
                            input.parentElement.insertBefore(newPreview, input.nextSibling);
                        }
                        
                        // Clear existing preview
                        preview.innerHTML = '';
                        
                        // Show new images
                        if (input.multiple) {
                            Array.from(input.files).forEach(file => {
                                const reader = new FileReader();
                                reader.onload = function(e) {
                                    const img = document.createElement('img');
                                    img.src = e.target.result;
                                    preview.appendChild(img);
                                };
                                reader.readAsDataURL(file);
                            });
                        } else if (input.files && input.files[0]) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                const img = document.createElement('img');
                                img.src = e.target.result;
                                preview.appendChild(img);
                            };
                            reader.readAsDataURL(input.files[0]);
                        }
                    }

                    // Add listeners to all file inputs
                    document.querySelectorAll('input[type="file"]').forEach(input => {
                        input.addEventListener('change', handleFileSelect);
                    });
                });
            </script>
            """
        ]
        blueprint.extra_css = [
            """
            <style>
                .hashtag-wrapper {
                    margin-bottom: 1rem;
                }
                .hashtag-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                    gap: 8px;
                    padding: 10px;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    background: #f8f9fa;
                }
                .hashtag-item {
                    background: white;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 6px 10px;
                }
                .hashtag-item:hover {
                    background: #e9ecef;
                }
                .checkbox-inline {
                    display: flex;
                    align-items: center;
                    margin: 0;
                    cursor: pointer;
                }
                .checkbox-inline input[type="checkbox"] {
                    margin-right: 8px;
                }
                /* Ensure proper form layout */
                .form-group {
                    margin-bottom: 1rem;
                }
                .control-label {
                    display: block;
                    margin-bottom: 0.5rem;
                    font-weight: bold;
                }
                /* Fix file upload fields */
                .form-control {
                    width: 100%;
                }
                .image-preview {
                    margin: 10px 0;
                    padding: 10px;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 5px;
                }
                .image-preview img {
                    height: 60px !important;
                    width: 60px !important;
                    object-fit: cover;
                    margin: 0;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    flex: 0 0 60px;
                }
                .existing-images {
                    margin-bottom: 10px;
                }
                .existing-images label {
                    display: block;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
            </style>
            """
        ]
        return blueprint

class HashtagForm(form.Form):
    name = fields.StringField('Name', [DataRequired()])

class HashtagsView(ModelView):
    column_list = ('name',)
    column_sortable_list = ('name',)
    form = HashtagForm

def init_admin(app, mongo):
    # Initialize admin with custom base template
    admin.init_app(app, index_view=AdminHomeView())
    
    # Add views with explicit endpoint names
    admin.add_view(RestaurantsView(mongo.db.restaurants, 'Restaurants', endpoint='restaurants'))
    admin.add_view(HashtagsView(mongo.db.hashtags, 'Hashtags', endpoint='hashtags')) 