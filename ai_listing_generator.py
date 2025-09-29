# ai_listing_generator.py
"""
AI-Powered Photo Enhancement and Listing Generation for eBay Sellers
This module provides:
- Photo enhancement and background removal
- Product identification and categorization
- Automated listing generation with SEO optimization
- Price suggestions based on market analysis
- Title optimization for maximum visibility
"""

import os
import io
import base64
import json
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProductAnalysis:
    """Analysis results from photo processing"""
    category: str
    brand: Optional[str]
    model: Optional[str]
    condition: str
    key_features: List[str]
    color: str
    material: Optional[str]
    confidence: float

@dataclass
class ListingContent:
    """Generated listing content"""
    title: str
    description: str
    category_id: str
    suggested_price: float
    price_range: Tuple[float, float]
    keywords: List[str]
    bullet_points: List[str]
    shipping_weight: Optional[float]
    dimensions: Optional[Dict[str, float]]

@dataclass
class PhotoEnhancement:
    """Enhanced photo results"""
    enhanced_image: bytes
    background_removed: bytes
    thumbnail: bytes
    quality_score: float
    recommendations: List[str]

class AIPhotoEnhancer:
    """AI-powered photo enhancement system"""
    
    def __init__(self):
        self.supported_formats = ['JPEG', 'JPG', 'PNG', 'WEBP']
        self.max_image_size = (2048, 2048)
        self.thumbnail_size = (300, 300)
    
    def enhance_photo(self, image_data: bytes) -> PhotoEnhancement:
        """Enhance a product photo for eBay listing"""
        try:
            # Load and validate image
            image = Image.open(io.BytesIO(image_data))
            if image.format not in self.supported_formats:
                raise ValueError(f"Unsupported format: {image.format}")
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
            
            # Enhance image quality
            enhanced_image = self._enhance_quality(image)
            
            # Create background-removed version
            bg_removed = self._remove_background(enhanced_image)
            
            # Create thumbnail
            thumbnail = enhanced_image.copy()
            thumbnail.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(enhanced_image)
            
            # Generate recommendations
            recommendations = self._generate_photo_recommendations(image, quality_score)
            
            # Convert to bytes
            enhanced_bytes = self._image_to_bytes(enhanced_image)
            bg_removed_bytes = self._image_to_bytes(bg_removed) if bg_removed else enhanced_bytes
            thumbnail_bytes = self._image_to_bytes(thumbnail)
            
            return PhotoEnhancement(
                enhanced_image=enhanced_bytes,
                background_removed=bg_removed_bytes,
                thumbnail=thumbnail_bytes,
                quality_score=quality_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Photo enhancement failed: {e}")
            raise
    
    def _enhance_quality(self, image: Image.Image) -> Image.Image:
        """Apply quality enhancements to the image"""
        enhanced = image.copy()
        
        # Enhance sharpness slightly
        sharpness = ImageEnhance.Sharpness(enhanced)
        enhanced = sharpness.enhance(1.1)
        
        # Enhance contrast slightly
        contrast = ImageEnhance.Contrast(enhanced)
        enhanced = contrast.enhance(1.05)
        
        # Enhance color saturation slightly
        color = ImageEnhance.Color(enhanced)
        enhanced = color.enhance(1.1)
        
        # Reduce noise with a gentle filter
        enhanced = enhanced.filter(ImageFilter.SMOOTH_MORE)
        
        return enhanced
    
    def _remove_background(self, image: Image.Image) -> Optional[Image.Image]:
        """Remove background from product photo (simplified implementation)"""
        try:
            # Convert PIL to OpenCV
            img_array = np.array(image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Simple background removal using GrabCut
            height, width = img_cv.shape[:2]
            
            # Create rectangle around the center (assuming product is centered)
            rect = (width//6, height//6, width*2//3, height*2//3)
            
            # Initialize masks
            mask = np.zeros((height, width), np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # Apply GrabCut
            cv2.grabCut(img_cv, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            
            # Create final mask
            final_mask = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # Apply mask
            result = img_cv * final_mask[:, :, np.newaxis]
            
            # Convert back to PIL with transparency
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            result_pil = Image.fromarray(result_rgb)
            
            # Add alpha channel for transparency
            result_rgba = Image.new('RGBA', result_pil.size, (255, 255, 255, 0))
            result_rgba.paste(result_pil, (0, 0))
            
            # Make background transparent
            data = np.array(result_rgba)
            rgb = data[:, :, :3]
            alpha = final_mask * 255
            data[:, :, 3] = alpha
            
            return Image.fromarray(data, 'RGBA')
            
        except Exception as e:
            logger.warning(f"Background removal failed: {e}")
            return None
    
    def _calculate_quality_score(self, image: Image.Image) -> float:
        """Calculate image quality score (0-1)"""
        try:
            img_array = np.array(image)
            
            # Check resolution
            width, height = image.size
            resolution_score = min((width * height) / (800 * 600), 1.0)
            
            # Check sharpness (using Laplacian variance)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            sharpness_score = min(cv2.Laplacian(gray, cv2.CV_64F).var() / 1000, 1.0)
            
            # Check brightness (not too dark or bright)
            brightness = np.mean(img_array)
            brightness_score = 1.0 - abs(brightness - 128) / 128
            
            # Weighted average
            quality_score = (
                resolution_score * 0.4 +
                sharpness_score * 0.4 +
                brightness_score * 0.2
            )
            
            return min(max(quality_score, 0.0), 1.0)
            
        except Exception:
            return 0.5  # Default score
    
    def _generate_photo_recommendations(self, image: Image.Image, quality_score: float) -> List[str]:
        """Generate recommendations for improving the photo"""
        recommendations = []
        
        width, height = image.size
        
        if quality_score < 0.6:
            recommendations.append("📸 Consider taking a higher quality photo with better lighting")
        
        if width < 800 or height < 600:
            recommendations.append("📏 Image resolution is low - use at least 800x600 pixels")
        
        if width != height:
            recommendations.append("🔲 Consider cropping to a square aspect ratio for better eBay display")
        
        # Check if image is too dark or bright
        img_array = np.array(image)
        brightness = np.mean(img_array)
        
        if brightness < 80:
            recommendations.append("💡 Image appears dark - try better lighting or increase brightness")
        elif brightness > 200:
            recommendations.append("☀️ Image appears overexposed - reduce lighting or decrease exposure")
        
        # Check for blur (simplified)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if blur_score < 100:
            recommendations.append("🎯 Image appears blurry - ensure camera is focused and steady")
        
        if not recommendations:
            recommendations.append("✅ Photo quality looks good!")
        
        return recommendations
    
    def _image_to_bytes(self, image: Image.Image, format: str = 'JPEG', quality: int = 95) -> bytes:
        """Convert PIL Image to bytes"""
        buffer = io.BytesIO()
        if format == 'JPEG' and image.mode in ('RGBA', 'LA'):
            # Convert to RGB for JPEG
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                rgb_image.paste(image, mask=image.split()[-1])
            else:
                rgb_image.paste(image)
            image = rgb_image
        
        image.save(buffer, format=format, quality=quality, optimize=True)
        return buffer.getvalue()

class ProductIdentifier:
    """AI product identification and categorization"""
    
    def __init__(self):
        # Category mapping for eBay
        self.category_mapping = {
            'electronics': {
                'smartphones': '9355',
