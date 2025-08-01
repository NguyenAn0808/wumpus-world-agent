from abc import ABC, abstractmethod
import pygame
import random

class Screen():
    def __init__(self, app=None):
        self.app = app
        self.popups = []
        self.sand_surface = None

    @abstractmethod
    def render(self):
        pass

    @abstractmethod
    def handle_input(self):
        pass