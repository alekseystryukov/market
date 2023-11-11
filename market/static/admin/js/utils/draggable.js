django.jQuery(document).ready(function () {

  const imgElement = django.jQuery('<img>').attr('src', draggableImageUrl).attr('alt', 'Drag and drop button').addClass('dragImage');

  django.jQuery('.drag-and-drop').each(function(obj){
    // Get draggable fields
    let fields = django.jQuery(this).find('.form-row').each(function(obj){
      let label = django.jQuery(this).find('label')
      label.before(imgElement.clone()) // insert draggable icons
    });
    
    // Sort fields from the highest to the lowest
    fields.sort(function(a, b){
      return django.jQuery(b).find('input').val() - django.jQuery(a).find('input').val();
    })
    
    // Add container for dragging fields
    django.jQuery(this).append('<div class="sortable"></div>')
    
    let sortable = django.jQuery(this).find('.sortable')
    
    sortable.html(fields)
    sortable.sortable({
      // Sortable requires `static/js/jquery-1-12-1-ui-min.js`
      stop: function (event, ui) {
        // Recalculate all inputs values
        sortable.find('.form-row').each(function (index) {
          // Value calculates in reversed order due sorting from the highest to the lowest
          django.jQuery(this).find('input').val(fields.length - index - 1);
        });
      }
    })
  })
});