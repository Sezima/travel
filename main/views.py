from datetime import timedelta

from django.contrib import messages
from django.db.models import Q
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, DeleteView

from .forms import TourForm, ImageForm
from .models import *


class MainPageView(ListView):
    model = Tour
    template_name = 'index.html'
    context_object_name = 'tours'
    paginate_by = 2

    def get_template_names(self):
        template_name = super(MainPageView, self).get_template_names()
        search = self.request.GET.get('q')
        if search:
            template_name = 'search.html'
        return template_name

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('q')
        filter = self.request.GET.get('filter')
        if search:
            context['tours'] = Tour.objects.filter(Q(title__icontains=search)|Q(description__icontains=search))
        elif filter:
            start_date = timezone.now() - timedelta(days=1)
            context['tours'] = Tour.objects.filter(post__gte=start_date)
        else:
            context['tours'] = Tour.objects.all()
        return context



def region_detail(request, slug):
    region = Region.objects.get(slug=slug)
    tours = Tour.objects.filter(region_id=slug)
    return render(request, 'region_detail.html', locals())
# start
# class RegionDetailView(DetailView):
#     model = Region
#     template_name = 'region_detail.html'
#     context_object_name = 'region'
#
#     def get(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         self.slug = kwargs.get('slug', None)
#         return super().get(request, *args, **kwargs)
#
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['tours'] = Tour.objects.filter(region_id=self.slug)
#         return context
# end

def detail(request, pk):
    tour = get_object_or_404(Tour, pk=pk)
    images = tour.images.all()
    return render(request, 'tour_detail.html', locals())


class TourDetailView(DetailView):
    model = Tour
    template_name = 'tour_detail.html'
    context_object_name = 'detail'
    paginate_by = 1
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        image = self.get_object().get_image
        context['images'] = self.get_object().images.exclude(id=image.id)
        return context

def add_tour(request):
    ImageFormSet = modelformset_factory(Image, form=ImageForm, max_num=5)
    if request.method == 'POST':
        tour_form = TourForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
        if tour_form.is_valid() and formset.is_valid():
            tour = tour_form.save()

            for form in formset.cleaned_data:
                image = form['image']
                Image.objects.create(image=image, tour=tour)

            return redirect(tour.get_absolute_url())
    else:
        tour_form = TourForm()
        formset = ImageFormSet(queryset=Image.objects.none())
    return render(request, 'add-tour.html', locals())


def update_tour(request, pk):
    tour = get_object_or_404(Tour, pk=pk)
    ImageFormSet = modelformset_factory(Image, form=ImageForm, max_num=5)
    tour_form = TourForm(request.POST or None, instance=tour)
    formset = ImageFormSet(request.POST or None, request.FILES or None, queryset=Image.objects.filter(tour=tour))
    if tour_form.is_valid() and formset.is_valid():
        tour = tour_form.save()

        for form in formset:
            image = form.save(commit=False)
            image.tour = tour
            image.save()
            return redirect(tour.get_absolute_url())
    return render(request, 'update-tour.html', locals())


class DeleteTourView(DeleteView):
    model = Tour
    template_name = 'delete-tour.html'
    success_url = reverse_lazy('home')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.add_message(request, messages.SUCCESS, 'Successfully deleted! ')
        return HttpResponseRedirect(success_url)


