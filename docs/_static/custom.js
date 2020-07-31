$(document).ready(function () {
  var sections = $('div.section');
  var activeLink = null;
  var bottomHeightThreshold = $(document).height() - 30;

  $(window).scroll(function (event) {
    var distanceFromTop = $(this).scrollTop();
    var currentSection = null;

    if(distanceFromTop + window.innerHeight > bottomHeightThreshold) {
      currentSection = $(sections[sections.length - 1]);
    }
    else {
      sections.each(function () {
        var section = $(this);
        if (section.offset().top - 1 < distanceFromTop) {
          currentSection = section;
        }
      });
    }

    if (activeLink) {
      activeLink.parent().removeClass('active');
    }

    if (currentSection) {
      activeLink = $('.sphinxsidebar a[href="#' + currentSection.attr('id') + '"]');
      activeLink.parent().addClass('active');
    }
  });
});
